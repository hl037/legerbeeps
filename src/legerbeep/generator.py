import datetime as dt
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from typing import Iterable, Callable, Any
import wave

def gen_beep(duration, freq, rate):
  samples = np.arange(int(rate * duration), dtype=np.float64)
  soft_start = np.arange(int(rate * 0.05), dtype=np.float64)
  soft_start /= len(soft_start)
  beep = np.sin(2 * np.pi * freq * samples / rate)
  beep[0:len(soft_start)] *= soft_start
  beep[-len(soft_start):] *= np.flip(soft_start)
  return beep

def gen_table_steps(start_speed, end_speed, speed_inc, distance, level_time):
  i = 0
  missing_metters = 0
  current_time = 0.
  level_speed = start_speed
  k = 0
  while level_speed < end_speed :
    j = 0
    level_speed_m_s = level_speed / 3.6
    next_level = current_time + level_time
    current_time += missing_metters / level_speed_m_s
    while current_time <= next_level :
      yield (i, j, level_speed, current_time)
      i += 1
      j += 1
      current_time += distance / level_speed_m_s
    missing_metters = (current_time - next_level) * level_speed_m_s
    current_time = next_level
    k += 1
    level_speed = start_speed + k * speed_inc

def np_to_wav_data(a:np.array):
  return (a * (2 ** 15 - 1)).astype("<h").tobytes()


@dataclass
class InfoSound(object):
  data: np.array
  priority: int
  t: float = None
  f: int = None


def place_info_sounds(sounds:Iterable[InfoSound], start: int, end: int):
  sounds_sorted = list(sounds)
  sounds_sorted.sort(key=lambda X: (-X.priority, X.f))
  space = end - start
  while sum(len(X.data) // 2 for X in sounds_sorted) > space :
    sounds_sorted.pop(0)
  sounds_sorted.sort(key=lambda X: (X.f, -X.priority))
  res = []
  f = end
  while sounds_sorted :
    s = sounds_sorted.pop()
    f = max(min(f - len(s.data) // 2, s.f), start + sum( len(ss.data) // 2 for ss in sounds_sorted ))
    res.insert(0, InfoSound(f=f, data=s.data, priority=s.priority))
  return res
        
    
  
class BeepWriter(object):
  def __init__(
    self,
    f:wave.Wave_write,
    beep_duration: float,
    beep_freq: float,
    rate: int
  ):
    self.f = f
    self.beep = np_to_wav_data(gen_beep(beep_duration, beep_freq, rate))
    self.rate = rate
    self.pos = 0
    self.offset = 0

  def write_beeps(self, table:Iterable[tuple[int, int, int, float]]):
    for i, j, level, time in table :
      self.write_silence_to(time)
      self.write_beep()

  def frame(self, time:float):
    return int(round(time * self.rate + self.offset))

  def patch_info_sound_generator(self, info_sound_gen:Iterable[InfoSound]):
    return (
      InfoSound(
        t=x.t,
        f=self.frame(x.t),
        data=x.data,
        priority=x.priority
      )
      for x in info_sound_gen
    )

  def write_beeps_with_info(
    self,
    table:Iterable[tuple[int, int, int, float]],
    info_sound_genenerators: Iterable[InfoSound]
  ):
    info_gen = [ self.patch_info_sound_generator(g) for g in info_sound_genenerators ]
    next_info = [ next(g, None) for g in info_gen ]
    for i, j, level, time in table :
      f = self.frame(time)
      info_to_place = []
      for k in range(len(info_gen)) :
        if next_info[k] is not None and next_info[k].f < f + len(self.beep) :
          info_to_place.append(next_info[k])
          next_info[k] = next(info_gen[k], None)
      placed_info = place_info_sounds(info_to_place, self.pos, f)
      for s in placed_info :
        self.write_silence_to(f = s.f)
        self.write_data(s.data)
      self.write_silence_to(f=f)
      self.write_beep()

  def write_silence_to(self, t: float=None, f:float=None):
    if f is None :
      if t is None :
        raise ValueError('f and t cannot be both None')
      f = self.frame(t)
    length = f - self.pos
    if length :
      data = np_to_wav_data(np.zeros(length))
      self.write_data(data)

  def write_beep(self):
    self.write_data(self.beep)

  def write_data(self, data):
    self.f.writeframes(data)
    self.pos += len(data) // 2

  def write_start_data(self, data):
    self.f.writeframes(data)
    self.pos += len(data) // 2
    self.offset += len(data) // 2
    

def load_sound_data(path:Path, rate:int):
  with wave.open(str(path), 'rb') as wf :
    wf: wave.Wave_read
    if wf.getnchannels() != 1 :
      raise RuntimeError('Cannot open wav with other than 1 channel')
    if wf.getsampwidth() != 2 :
      raise RuntimeError('Cannot open wav with sample width other than 2')
    if wf.getframerate() != rate :
      raise RuntimeError('Framerate should be the same as the output : {rate}')
    return wf.readframes(wf.getnframes())


def step_info_generator(steps_str:str, data_path:Path, level_duration:float, rate:int):
  steps = map(float, steps_str.split(','))
  step_data = [
    (s, load_sound_data(data_path / f'{s}s.wav', rate))
    for s in steps
  ]
  i = 0
  t = 0
  while True :
    for s, data in step_data :
      yield InfoSound(
        t=t + s,
        data=data,
        priority=10
      )
    i += 1
    t = level_duration * i

def level_info_generator(levels:Iterable[float], data_path:Path, level_duration:float, rate:int):
  i = 1
  t = level_duration
  for l in levels :
    yield InfoSound(
      t=t,
      data=load_sound_data(data_path / f'{l}.wav', rate),
      priority=5,
    )
    i += 1
    t = level_duration * i
  

def wav_gen(
  frequency,
  beeplength,
  distance,
  leveltime,
  startspeed,
  speedincrement,
  endspeed,
  rate,
  printoffset,
  datapath,
  steps,
  with_start_msg,
  output,
):
  table = list(gen_table_steps(startspeed, endspeed, speedincrement, distance, leveltime))
  levels = []
  for i, j, level, time in table :
    if level not in levels :
      levels.append(level)
  if output == '-' :
    for i, j, level, time in table :
      td = dt.timedelta(seconds=time+printoffset)
      print(f'{i:03d}: {td.seconds // 60:02d}\'{td.seconds % 60:02d}.{td.microseconds // 1000:03d} {level:>4} ({j:02d})')
    return
  with wave.open(output, 'wb') as wf :
    wf: wave.Wave_write
    wf.setnchannels(1)
    wf.setframerate(rate)
    wf.setsampwidth(2)
    writer = BeepWriter(wf, beeplength, frequency, rate)
    if with_start_msg :
      writer.write_start_data(load_sound_data(datapath / 'start.wav', rate))
    info_generators = []
    if datapath :
      info_generators.append(level_info_generator(levels[1:], datapath, leveltime, rate))
    if steps :
      info_generators.append(step_info_generator(steps, datapath, leveltime, rate))
    writer.write_beeps_with_info(table, info_generators)
    for i, j, level, time in table :
      td = dt.timedelta(seconds=time + printoffset + writer.offset // rate)
      print(f'{i:03d}: {td.seconds // 60:02d}\'{td.seconds % 60:02d}.{td.microseconds // 1000:03d} {level:>4} ({j:02d})')
      if level not in levels :
        levels.append(level)

  


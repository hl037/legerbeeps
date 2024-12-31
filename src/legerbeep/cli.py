import click
from pathlib import Path
from legerbeep.generator import wav_gen


@click.command(name="main")
@click.option('--frequency', '-f', type=float, default=440.)
@click.option('--beeplength', '-l', type=float, default=1.)
@click.option('--distance', '-d', type=float, default=20.)
@click.option('--leveltime', '-t', type=float, default=60.)
@click.option('--startspeed', '-s', type=float, default=8.)
@click.option('--speedincrement', '-i', type=float, default=0.5)
@click.option('--endspeed', '-e', type=float, default=20.)
@click.option('--rate', '-r', type=int, default=44100)
@click.option('--printoffset', '--po', type=float, default=0.)
@click.option('--datapath', type=str, default=None)
@click.option('--steps', type=str, default=None)
@click.option('--with-start-msg', is_flag=True)
@click.argument('output')
def main(
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
  try :
    wav_gen(
      frequency,
      beeplength,
      distance,
      leveltime,
      startspeed,
      speedincrement,
      endspeed,
      rate,
      printoffset,
      Path(datapath),
      steps,
      with_start_msg,
      output
    )
  except :
    import pdb; pdb.xpm()
    

if __name__ == "__main__" :
  main()
  

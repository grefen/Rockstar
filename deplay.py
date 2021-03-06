import subprocess
import scipy
import scipy.optimize
import math
import chess
import re
import csv
from chess import uci
from chess import Board
from chess import Move
from chess import pgn
from scipy.optimize import rosen, differential_evolution
from scipy.stats import pearsonr
import scipy

engine = 'stockfish.exe'
depth =  14
popsize = 15
multipv = 1

if popsize == None:
  popsize = 15

'''
def getPars():
  sf = subprocess.Popen([engine, '\n'],  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
  sf.stdin.write('isready' + '\n')
  pars = []
  outline = []
  while outline is not '':
    outline = sf.stdout.readline().rstrip()
    if not (outline.startswith('Stockfish ') or outline.startswith('Unknown ') or outline == ''):
      pars.append(outline.split(','))
  sf.terminate()
  sf.wait()
  return pars

'''
def get_pars():
  params = []
  f = open('result.csv')
  lines = f.read().split('\n')
  if lines[-1] == '':
    lines.remove('')

  for p in lines:
    params.append(p.split())
  
  return params

Pars = get_pars()

def Array2Pars(parsArray):
  locpars = Pars[:]
  for n, par in enumerate(locpars):
    locpars[n][1] = int(parsArray[n])
  return locpars

def Pars2Array(pars):
  parsArray = [int(par[1]) for par in pars] 
#  print(parsArray)
  return parsArray

def fitness(parsArray):
  locpars = Array2Pars(parsArray)
  diffs = launchSf(locpars)
  return -diffs
  
def getBounds():
  return [(-100, 100) for p in Pars]

def launchSf(locpars):
  sf = uci.popen_engine(engine)
  base = uci.popen_engine(engine)
  info_handler = uci.InfoHandler()
  info_handler1 = uci.InfoHandler()
  sf.info_handlers.append(info_handler)
  base.info_handlers.append(info_handler1)

  sf.setoption({'Clear Hash': True})
  sf.setoption({'Hash': 1})
  base.setoption({'Clear Hash': True})
  base.setoption({'Hash': 1})

  for p in locpars:
    sf.setoption({p[0]: p[1]})
  
  sf.uci()
  sf.isready()
  sf.ucinewgame()
  base.uci()
  base.isready()
  base.ucinewgame()
  board = Board(chess960=False)
#  board.set_epd('5rk1/p1pr2bp/1p2b1p1/2q1p3/2P1P3/1P1P1PQ1/P5BP/2BR1R1K b - - 9 23')
#  opening, play, evals = pgn_prepare()
#  print(opening)
#  for move in opening:
#    board.push_san(move)
#  sf.position(board)

  diffs = 0
#  diffs1 = []
#  evs = []
  for j in range(2):
#    i=0   
    try:
      while True:
        if board.turn == 1:
          pos = board
          sf.position(pos)
          pos.push(sf.go(depth=14)[0])
          score = info_handler.info["score"][1].cp
#         print(info_handler.info["score"])
          if info_handler.info["score"][1].mate is not None:
            break
          if pos.is_game_over(claim_draw=True) is True:
            break
          diffs += score
        else:
          pos = board
          base.position(pos)
          pos.push(base.go(depth=14)[0])
          if info_handler1.info["score"][1].mate is not None:
            break
          if pos.is_game_over(claim_draw=True) is True:
            break
#      i=i+1
    finally:
      break
    base.position(board)
    board.push(base.go(depth=12)[0])
  print(diffs)
  
  sf.terminate()

  return diffs

def pgn_prepare():
  pgn = open("test.pgn")
  game = chess.pgn.read_game(pgn)
  pgn.close ()
  game.headers["Event"]
  board = game.board()
  main = game.main_line()
#  print(main)
  variation = game.board().variation_san(main)
#  print(variation)
  node = game
  moves = []
  while not node.is_end():
    next_node = node.variation(0)
    move = node.board().san(next_node.move)
    board = node.board()
#    print(board)
    moves.append(move)
    node = next_node
  evals = re.findall(r'wv=(.*?),', str(game))
  start = len(moves) - len(evals)
  play = moves[start:]
  opening = moves[0:start]
  evals = [float(a) for a in evals]
  dictionary = [{a: float(b)} for a,b in zip(play, evals)]
  return opening, play, evals

def statusMsg(xk, convergence = 1):
  newPars = Array2Pars(xk)
  print
  for p in newPars:
    print( p[0],p[1])
  print
  return False

if __name__ == '__main__':
  f = fitness(Pars2Array(Pars))
  print( '\n' +  'Reference correlation: ' + str(f))
  res = scipy.optimize.differential_evolution(fitness, getBounds(), disp=True, tol = 5, callback = statusMsg, popsize = 20, strategy = 'best1bin', init = 'random', polish = False)
  statusMsg(res.x)
  print( 'Search/eval correlation: ', -res.fun)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import logging
import random
import webapp2
import numpy as np
import signal
import time

BOARD = np.array([[ 30, -12,   0,  -1,  -1,   0, -12,  30],
                  [-12, -15,  -3,  -3,  -3,  -3, -15, -12],
                  [  0,  -3,   0,  -1,  -1,   0,  -3,   0],
                  [ -1,  -3,  -1,  -1,  -1,  -1,  -3,  -1],
                  [ -1,  -3,  -1,  -1,  -1,  -1,  -3,  -1],
                  [  0,  -3,   0,  -1,  -1,   0,  -3,   0],
                  [-12, -15,  -3,  -3,  -3,  -3, -15, -12],
                  [ 30, -12,   0,  -1,  -1,   0, -12,  30]])
BOARD_2 = np.array([[ 45, -11,  4, -1, -1,  4, -11,  45],
                    [-11, -16, -1, -3, -3, -1, -16, -11],
                    [  4,  -1,  2, -1, -1,  2,  -1,   4],
                    [ -1,  -3, -1,  0,  0, -1,  -3,  -1],
                    [ -1,  -3, -1,  0,  0, -1,  -3,  -1],
                    [  4,  -1,  2, -1, -1,  2,  -1,   4],
                    [-11, -16, -1, -3, -3, -1, -16, -11],
                    [ 45, -11,  4, -1, -1,  4, -11,  45]])

BOARD_FIN = np.ones((8,8))

# Reads json description of the board and provides simple interface.
class Game:
	# Takes json or a board directly.
	def __init__(self, body=None, board=None):
                if body:
		        game = json.loads(body)
                        self._board = game["board"]
                else:
                        self._board = board

	# Returns piece on the board.
	# 0 for no pieces, 1 for player 1, 2 for player 2.
	# None for coordinate out of scope.
	def Pos(self, x, y):
		return Pos(self._board["Pieces"], x, y)

	# Returns who plays next.
	def Next(self):
		return self._board["Next"]

	# Returns the array of valid moves for next player.
	# Each move is a dict
	#   "Where": [x,y]
	#   "As": player number
	def ValidMoves(self):
                moves = []
                for y in xrange(1,9):
                        for x in xrange(1,9):
                                move = {"Where": [x,y],
                                        "As": self.Next()}
                                if self.NextBoardPosition(move):
                                        moves.append(move)
                return moves
                                

	# Helper function of NextBoardPosition.  It looks towards
	# (delta_x, delta_y) direction for one of our own pieces and
	# flips pieces in between if the move is valid. Returns True
	# if pieces are captured in this direction, False otherwise.
	def __UpdateBoardDirection(self, new_board, x, y, delta_x, delta_y):
		player = self.Next()
		opponent = 3 - player
		look_x = x + delta_x
		look_y = y + delta_y
		flip_list = []
		while Pos(new_board, look_x, look_y) == opponent:
			flip_list.append([look_x, look_y])
			look_x += delta_x
			look_y += delta_y
		if Pos(new_board, look_x, look_y) == player and len(flip_list) > 0:
                        # there's a continuous line of our opponents
                        # pieces between our own pieces at
                        # [look_x,look_y] and the newly placed one at
                        # [x,y], making it a legal move.
			SetPos(new_board, x, y, player)
			for flip_move in flip_list:
				flip_x = flip_move[0]
				flip_y = flip_move[1]
				SetPos(new_board, flip_x, flip_y, player)
                        return True
                return False

	# Takes a move dict and return the new Game state after that move.
	# Returns None if the move itself is invalid.
	def NextBoardPosition(self, move):
		x = move["Where"][0]
		y = move["Where"][1]
                if self.Pos(x, y) != 0:
                        # x,y is already occupied.
                        return None
		new_board = copy.deepcopy(self._board)
                pieces = new_board["Pieces"]

		if not (self.__UpdateBoardDirection(pieces, x, y, 1, 0)
                        | self.__UpdateBoardDirection(pieces, x, y, 0, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 0)
		        | self.__UpdateBoardDirection(pieces, x, y, 0, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, -1)):
                        # Nothing was captured. Move is invalid.
                        return None
                
                # Something was captured. Move is valid.
                new_board["Next"] = 3 - self.Next()
		return Game(board=new_board)

# Returns piece on the board.
# 0 for no pieces, 1 for player 1, 2 for player 2.
# None for coordinate out of scope.
#
# Pos and SetPos takes care of converting coordinate from 1-indexed to
# 0-indexed that is actually used in the underlying arrays.
def Pos(board, x, y):
	if 1 <= x and x <= 8 and 1 <= y and y <= 8:
		return board[y-1][x-1]
	return None

# Set piece on the board at (x,y) coordinate
def SetPos(board, x, y, piece):
	if x < 1 or 8 < x or y < 1 or 8 < y or piece not in [0,1,2]:
		return False
	board[y-1][x-1] = piece

# Debug function to pretty print the array representation of board.
def PrettyPrint(board, nl="<br>"):
	s = ""
	for row in board:
		for piece in row:
			s += str(piece)
		s += nl
	return s

def PrettyMove(move):
	m = move["Where"]
	return '%s%d' % (chr(ord('A') + m[0] - 1), m[1])

def signal_handler(signum, frame):
        raise Exception('time out')
                
class MainHandler(webapp2.RequestHandler):
    # Handling GET request, just for debugging purposes.
    # If you open this handler directly, it will show you the
    # HTML form here and let you copy-paste some game's JSON
    # here for testing.

    def get(self):
        if not self.request.get('json'):
          self.response.write("""
<body><form method=get>
Paste JSON here:<p/><textarea name=json cols=80 rows=24></textarea>
<p/><input type=submit>
</form>
</body>
""")
          return
        else:
          g = Game(self.request.get('json'))
          self.pickMove2(g)

    def post(self):
    	# Reads JSON representation of the board and store as the object.
    	g = Game(self.request.body)
        # Do the picking of a move and print the result.
        self.pickMove2(g)

    def pickMove2(self, g):
    	# Gets all valid moves.
    	valid_moves = g.ValidMoves()
        start = time.time()
    	if len(valid_moves) == 0:
    		# Passes if no valid moves.
    		self.response.write("PASS")
    	else:
                self.empty = np.sum([[1 if g.Pos(x, y) == 0 else 0 for x in xrange(1,9)] for y in xrange(1,9)])
                self.best_point = {1:{}, 2:{}, 3:{}, 4:{}, 5:{}, 6:{}, 7:{}, 8:{}, 9:{}, 10:{}, 11:{}, 12:{}, 13:{}, 14:{}}
                self.threshold0 = 13
                self.threshold1 = 16
                self.threshold2 = 24
                if self.empty < self.threshold0:
                        result = self.choose_final(g, min(6, self.empty), g.Next(), [0])
                elif self.empty < self.threshold1:
                        result = self.choose_final(g, 4, g.Next(), [0])
                elif self.empty < self.threshold2:
                        result = self.choose_final(g, 3, g.Next(), [0])
                else:
                        if len(g.ValidMoves()) < 7:
                                result = self.choose(g, 3, g.Next(), [0])
                        else:
                                result = self.choose(g, 2, g.Next(), [0])
    		move = result['best_move']
                self.response.write(PrettyMove(move))
        elapsed_time = time.time()-start
        logging.info(elapsed_time)

    def choose(self, g, depth, next, index, open_point=0):
        validmove = g.ValidMoves()
        if depth == 0:
            final_open = 0
            if validmove:
                    for move in validmove:
                            open = self.calculateOpenness(g, g.NextBoardPosition(move))
                            if open < final_open:
                                    final_open = open
            if g.Next() != next:
                    final_open *= -1
            logging.info("open_point%d, final_open%d", open_point, final_open)
            return {'point': self.calculatePoint(g, next) + 3*(open_point + final_open), 'best_move': None}
        
        if not validmove:
            if g.Next() == next:
                return {'point': 100, 'best_move': None}
            else:
                return {'point': -100, 'best_move': None}
        
        best_move = random.choice(validmove)
        if g.Next() == next: # next is me 
            point = -100
            for i, move in enumerate(validmove):
                new_index = [i] + index 
                g_next = g.NextBoardPosition(move)
                openness = self.calculateOpenness(g, g_next)
                result = self.choose(g_next, depth - 1, next, new_index, open_point + openness)
                logging.info(move)
                logging.info("result%d, depth%d", result['point'], depth)
                self.best_point[depth-1] = {}
                if not self.best_point[depth].has_key(new_index[1]):
                        self.best_point[depth][new_index[1]] = result['point']
                if len(new_index) > 2:
                        if self.best_point[depth + 1].has_key(new_index[2]):
                                if result['point'] > self.best_point[depth+1][new_index[2]]:
                                        #logging.info("cut")
                                        #self.best_point[depth][new_index[1]] = result['point']
                                        point = result['point']
                                        best_move = move
                                        break
                if result['point'] > point:
                        point = result['point']
                        best_move = move
                        self.best_point[depth][new_index[1]] = result['point']
                #logging.info("point%d, depth%d", point, depth)
                #logging.info(self.best_point)
                        
        elif g.Next() != next: # next is enemy
            point = 100
            for i, move in enumerate(validmove):
                new_index = [i] + index
                #logging.info(new_index)
                g_next = g.NextBoardPosition(move)
                openness = self.calculateOpenness(g, g_next)
                result = self.choose(g_next, depth - 1, next, new_index, open_point - openness)
                logging.info(move)
                logging.info("result%d, depth%d", result['point'], depth)
                #logging.info("point%d", result['point'])
                self.best_point[depth-1] = {}
                if not self.best_point[depth].has_key(new_index[1]):
                        self.best_point[depth][new_index[1]] = result['point']
                if len(new_index) > 2:
                        if self.best_point[depth + 1].has_key(new_index[2]):
                                if result['point'] < self.best_point[depth+1][new_index[2]]:
                                        logging.info("short")
                                        point = result['point']
                                        best_move = move
                                        #self.best_point[depth][new_index[1]] = result['point']
                                        break
                if result['point'] < point:
                    point = result['point']
                    best_move = move
                    self.best_point[depth][new_index[1]] = result['point']
                #logging.info("point%d, depth%d", point, depth)
                #logging.info(self.best_point)
        return {'point': point, 'best_move': best_move}

    def choose_final(self, g, depth, next, index):
        validmove = g.ValidMoves()
        #logging.info(validmove)
        if depth == 0:
                logging.info(next==g.Next())
                if self.empty < self.threshold0:
                        board_me = np.array([[1 if g.Pos(x, y) == next else 0 for x in xrange(1,9)] for y in xrange(1,9)])
                        board_enemy = np.array([[1 if g.Pos(x, y) not in [next, 0] else 0 for x in xrange(1,9)] for y in xrange(1,9)])
                        point = np.sum(board_me * BOARD_FIN) - np.sum(board_enemy * BOARD_FIN)
                else:
                        point = self.calculatePoint(g, next)
                logging.info(point)
                return {'point': point, 'best_move': None}
        
        if not validmove:
            if g.Next() == next:
                return {'point': 100, 'best_move': None}
            else:
                return {'point': -100, 'best_move': None}
        
        best_move = random.choice(validmove)
        if g.Next() == next: # next is me 
            point = -100
            for i, move in enumerate(validmove):
                new_index = [i] + index 
                g_next = g.NextBoardPosition(move)
                result = self.choose_final(g_next, depth - 1, next, new_index)
                self.best_point[depth-1] = {}
                if not self.best_point[depth].has_key(new_index[1]):
                        self.best_point[depth][new_index[1]] = result['point']
                if len(new_index) > 2:
                        if self.best_point[depth + 1].has_key(new_index[2]):
                                if result['point'] > self.best_point[depth+1][new_index[2]]:
                                        logging.info("cut")
                                        point = result['point']
                                        best_move = move
                                        break
                if result['point'] > point:
                        point = result['point']
                        best_move = move
                        self.best_point[depth][new_index[1]] = result['point']

        elif g.Next() != next: # next is enemy
            point = 100
            for i, move in enumerate(validmove):
                new_index = [i] + index
                g_next = g.NextBoardPosition(move)
                result = self.choose_final(g_next, depth - 1, next, new_index)
                self.best_point[depth-1] = {}
                if not self.best_point[depth].has_key(new_index[1]):
                        self.best_point[depth][new_index[1]] = result['point']
                if len(new_index) > 2:
                        if self.best_point[depth + 1].has_key(new_index[2]):
                                if result['point'] < self.best_point[depth+1][new_index[2]]:
                                        logging.info("short")
                                        point = result['point']
                                        best_move = move
                                        break
                if result['point'] < point:
                    point = result['point']
                    best_move = move
                    self.best_point[depth][new_index[1]] = result['point']
        return {'point': point, 'best_move': best_move}


    def calculatePoint(self, h, next):
        # more is better
        #logging.info(next==h.Next())
        board_me = np.array([[1 if h.Pos(x, y) == next else 0 for x in xrange(1,9)] for y in xrange(1,9)])
        board_enemy = np.array([[1 if h.Pos(x, y) not in [next, 0] else 0 for x in xrange(1,9)] for y in xrange(1,9)])
        point = np.sum(board_me * BOARD_2) - np.sum(board_enemy * BOARD_2)
        logging.info("calculate%d", point)
        if h.Next() == next:
                point += len(h.ValidMoves())
        else:
                point -= len(h.ValidMoves())
        logging.info("len%d", len(h.ValidMoves()))
        return point

    def calculateOpenness(self, h, h_next):
        change_list = [[x, y] if h.Pos(x, y) != h_next.Pos(x, y) and h.Pos(x, y) != 0 else [] for x in range(1, 9) for y in range(1, 9)]
        change_list = filter(lambda s:s != [], change_list)
        openness = 0
        for change in change_list:
                x, y = change
                openness += np.sum([1 if h.Pos(p, q) == 0 else 0 for p in xrange(max(x-1, 1), min(x+2, 9)) for q in xrange(max(y-1, 1), min(y+2, 9))])
        return openness * (-1)
                
app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)

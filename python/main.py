#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import copy
import json
import random
import webapp2

# Reads json description of the board and provides simple interface.
class Game:
	# Takes json.
	def __init__(self, body):
		self.board_ = json.loads(body)

	# Returns underlying board object.
	def Object(self):
		return self.board_

	# Returns piece on the board.
	# 0 for no pieces, 1 for player 1, 2 for player 2.
	# None for coordinate out of scope.
	def Pos(self, x, y):
		return Pos(self.board_["board"]["Pieces"], x, y)

	# Returns who plays next.
	def Next(self):
		return self.board_["board"]["Next"]

	# Returns the array of valid moves for next player.
	# Each move is a dict
	#   "Where": [x,y]
	#   "As": player number
	def ValidMoves(self):
		if self.board_["valid_moves"]:
			return self.board_["valid_moves"]
		return []

	# Helper function of NextBoardPosition.
	# It looks towards (delta_x, delta_y) direction and flip if valid.
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
		if Pos(new_board, look_x, look_y) == player:
			SetPos(new_board, x, y, player)
			for flip_move in flip_list:
				flip_x = flip_move[0]
				flip_y = flip_move[1]
				SetPos(new_board, flip_x, flip_y, player)

	# Takes a move dict and return the board positions after that move.
	# Returns None if the move itself is invalid.
	def NextBoardPosition(self, move):
		if move not in self.ValidMoves():
			return None
		x = move["Where"][0]
		y = move["Where"][1]
		new_board = copy.deepcopy(self.board_["board"]["Pieces"])

		self.__UpdateBoardDirection(new_board, x, y, 1, 0)
		self.__UpdateBoardDirection(new_board, x, y, 0, 1)
		self.__UpdateBoardDirection(new_board, x, y, -1, 0)
		self.__UpdateBoardDirection(new_board, x, y, 0, -1)
		self.__UpdateBoardDirection(new_board, x, y, 1, 1)
		self.__UpdateBoardDirection(new_board, x, y, -1, 1)
		self.__UpdateBoardDirection(new_board, x, y, 1, -1)
		self.__UpdateBoardDirection(new_board, x, y, -1, -1)

		return new_board

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

def ParseMove(move):
	m = move["Where"]
	return '%s%d' % (chr(ord('A') + m[0] - 1), m[1])

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

    def pickMove(self, g):
    	# Gets all valid moves.
    	valid_moves = g.ValidMoves()
    	if len(valid_moves) == 0:
    		# Passes if no valid moves.
    		self.response.write("PASS")
    	else:
    		# Chooses a valid move randomly if available.
	    	move = random.choice(g.ValidMoves())
    		self.response.write(ParseMove(move))

    def pickMove2(self, g):
    	# Gets all valid moves.
    	valid_moves = g.ValidMoves()
    	if len(valid_moves) == 0:
    		# Passes if no valid moves.
    		self.response.write("PASS")
    	else:
    		# Chooses a valid move randomly if available.
    		move = self.choose(g)
	    	# move = random.choice(g.ValidMoves())
    		self.response.write(ParseMove(move))

    def choose(self, g):
    	point = -100
    	for move in g.ValidMoves():
    		new_board = g.NextBoardPosition(move)
    		if self.calculatePoint(g, new_board) > point:
    			point = self.calculatePoint(g, new_board)
    			best_move = move
    	return best_move

    def calculatePoint(self, g, board):
    	point = 0
    	for y in range(1,9):
			for x in range(1,9):
				if Pos(board, x, y) == g.Next():
					if x in [1, 8] and y in [1, 8]:
						point += 5
					elif (x in [1, 8] and y in range(3, 7)) or (x in range(3, 7) and y in [1, 8]): 
						point += 3
					elif (x in [1, 8] and y in [2, 7]) or (x in [2, 7] and y in [1, 2, 7, 8]):
						point -= 5 
					elif (x in [2, 7] and y in range(3, 7)) or (x in range(3, 7) and y in [2, 7]):
						point -= 3
					else:
						point += 1 
	return point

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)

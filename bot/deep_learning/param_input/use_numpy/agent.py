import numpy as np
import random
from collections import deque
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from bot.deep_learning.param_input.use_numpy.model import Model
from bot.deep_learning.param_input.use_numpy.helper import plot
from game.game_core import Game

MAX_MEMORY = 100000
MAX_SAMPLE_SIZE = 1000
LEARNING_RATE = 0.01
GAMMA = 0.9
EPSILON = 1
EPSILON_DECAY = 0.95
MIN_EPSILON = 0.05
TRAINING_MODE = 1
PERFORM_MODE = 2

class Agent:

    def __init__(self, game: Game):
        self.number_of_games = 0
        self.memory = deque(maxlen=MAX_MEMORY)
        self.epsillon = EPSILON
        self.mode = TRAINING_MODE
        self.game = None #TODO
        self.model = Model(28, 256, 9, LEARNING_RATE) #warning: the number of neurals in first layer must match the size of game.get_state()
        self.game = game

    def set_mode(self, mode: int = TRAINING_MODE):
        self.mode = mode

    def get_state(self) -> np.ndarray: # get game state. example: array([1, 1, 0, 0, 0, 1, 0, ...0])
        return self.game.get_state()

    def get_move(self, state: np.ndarray) -> np.ndarray:
        move = np.zeros((9, ), dtype=np.float64)
        if self.mode == TRAINING_MODE:
            # decise to take a random move or not
            if random.random() < self.epsillon:
                # if yes pick a random move
                move[random.randint(0, 8)] = 1
            else:
                # if not model will predict the move
                move[np.argmax(self.model.forward(state)[2])] = 1
        elif self.mode == PERFORM_MODE:
            # always use model to predict move in pridict move / always predict
            move[np.argmax(self.model.forward(state)[2])] = 1
        return move

    def perform_action(self, action: np.ndarray): # call action api in game
        self.game.take_action(action)

    def get_reward(self) -> tuple[float, bool]: # return result: float, and game_over: bool
        return self.game.get_reward()
    
    def get_score(self) -> int:
        return self.game.score
    
    def restart_game(self):
        self.game.restart_game()

    def draw_game(self):
        self.game.draw()

    def train_short_memory(self, old_state: np.ndarray, action: np.ndarray, reward: float, new_state: np.ndarray):
        target = self.convert(old_state, action, reward, new_state)
        self.model.train(old_state, target)

    def train_long_memory(self):
        if len(self.memory) <= MAX_SAMPLE_SIZE:
            # if have not saved over 1000 states yet
            mini_sample = self.memory
        else:
            # else pick random 1000 states to re-train
            mini_sample = random.sample(self.memory, MAX_SAMPLE_SIZE)
        for old_state, action, reward, new_state in mini_sample:
            self.train_short_memory(old_state, action, reward, new_state)

    def remember(self, old_state: np.ndarray, action: np.ndarray, reward: float, new_state: np.ndarray):
        self.memory.append((old_state, action, reward, new_state))

    def convert(self, old_state: np.ndarray, action: np.ndarray, reward: float, new_state: np.ndarray) -> np.ndarray:
        # use simplified Bellman equation to calculate expected output
        target = self.model.forward(old_state)[2]
        Q_new = reward + GAMMA * np.max(self.model.forward(new_state)[2])
        target[np.argmax(action)] = Q_new
        return target

def train():
    game = Game()
    agent = Agent(game)

    scores = []

    while True:
        # get the current game state
        old_state = agent.get_state()

        # get the move based on the state
        action = agent.get_move(old_state)

        # perform action in game
        agent.perform_action(action)

        # get the new state after performed action
        new_state = agent.get_state()

        # get the reward of the action
        reward, game_over = agent.get_reward()

        # train short memory with the action performed
        agent.train_short_memory(old_state, action, reward, new_state)

        # remember the action and the reward
        agent.remember(old_state, action, reward, new_state)

        # if game over then train long memory and start again
        if game_over:
            # reduce epsilon / percentage of random move
            agent.epsillon /= EPSILON_DECAY
            agent.epsillon = max(agent.epsillon, MIN_EPSILON)

            # increase number of game and train long memory / re-train experience before start new game
            agent.number_of_games += 1
            agent.train_long_memory()

            if agent.number_of_games % 10 == 0:
                # save before start new game
                # agent.model.save()
                pass

            # save the score to plot
            scores.append(agent.get_score())
            plot(scores)

            agent.restart_game()

def perform():
    game = Game()
    agent = Agent(game)
    agent.set_mode(PERFORM_MODE)

    while True:
        # get the current game state
        state = agent.get_state()

        # get the model predict move
        action = agent.get_move(state)

        # perform selected move
        agent.perform_action(action)

        # check if game over or not
        _, game_over = agent.get_reward()

        # restart game if game over
        if game_over:
            agent.number_of_games += 1
            if agent.number_of_games % 10 == 0:
                agent.model.save()
            agent.restart_game()

        # use pygame to control FPS and UPS
        agent.game.clock.tick(60)


if __name__ == '__main__':
    mode = TRAINING_MODE

    if mode == TRAINING_MODE:
        train()
    elif mode == PERFORM_MODE:
        perform()
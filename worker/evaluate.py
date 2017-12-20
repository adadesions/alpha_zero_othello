from alpha_zero_othello.config import EvaluateConfig
from alpha_zero_othello.lib import tf_util, util
from alpha_zero_othello.player.player import RandomPlayer
from alpha_zero_othello.player.aiplayer import AIPlayer
from alpha_zero_othello.othello import Othello
from time import time, sleep
import glob

def start():
    config = EvaluateConfig()
    tf_util.update_memory(config.gpu_mem_fraction)

    
    models = glob.glob(config.data.model_location+"*.h5")
    if len(models) == 0:
        ai = AIPlayer(config.buffer_size, config.game.simulation_num_per_move)
        ai.save_weights(config.data.model_location+str(time())+".h5")
    start = time()
    run_games(config)
    print("Total Time: %0.2f seconds" % (time()-start))
             
    
def run_games(config):
    game = Othello()
    model_1 = ""
    model_2 = ""
    p1, new_1 = create_player(config.model_1, model_1, config)
    p2, new_2 = create_player(config.model_2, model_2, config)
    i = 0
    total = 0
    while True:
        i += 1
        new_1 = load_player(p1, config.model_1, model_1, config)
        new_2 = load_player(p2, config.model_2, model_2, config)
        while(new_1 == model_1 and new_2 == model_2):
            #print("Waiting on new model. Sleeping for 1 minute.")
            sleep(60)
            new_1 = load_player(p1, config.model_1, model_1, config)
            new_2 = load_player(p2, config.model_2, model_2, config)
        model_1 = new_1
        model_2 = new_2
        wins = 0
        losses = 0
        ties = 0
        print("Iteration %04d"%i)
        print("Playing %d games with %d simulations per move" % (config.game_num, config.game.simulation_num_per_move))
        start=time()
        for j in range(config.game_num):
            util.progress(j, config.game_num, start=start)
            side = -1
            turn = 1
            while not game.game_over():
                tau = config.game.tau_1
                if config.game.tau_swap < turn:
                    tau = config.game.tau_2
                if j % 2 == 0:
                    if side == -1:
                        t = p1.pick_move(game, side, tau=tau)
                    else:
                        t = p2.pick_move(game, side, tau=tau)
                else:
                    if side == 1:
                        t = p1.pick_move(game, side, tau=tau)
                    else:
                        t = p2.pick_move(game, side, tau=tau)
                game.play_move(t[0], t[1], side)
                side *= -1
                turn += 1
            if game.get_winner() == 0:
                ties += 1
            elif j % 2 == 0 and game.get_winner() == -1:
                wins += 1
            elif j % 2 == 1 and game.get_winner() == 1:
                wins += 1
            else:
                losses += 1
            game.reset_board()
        util.progress(config.game_num, config.game_num, start=start)
        print("%s vs %s: wins -> %0.2f%% ties -> %0.2f%% losses -> %0.2f%% out of %d games" % (config.model_1, config.model_2, 
              100*wins/config.game_num, 100*ties/config.game_num, 100*losses/config.game_num, config.game_num))
        total += 100*wins/config.game_num
        print("Average Win Percent: %0.2f%%" % (total/i))
        if not (config.repeat_with_new_model and (config.model_1 == "newest" or config.model_2 == "newest")):
            break
        
def create_player(player_name, current, config):
    if player_name == "random":
        model = "random"
        player = RandomPlayer()
    elif player_name == "newest":
        model = sorted(glob.glob(config.data.model_location+"*.h5"))[-1]
        if model != current:
            print("Loading new model: %s" % model)
        player = AIPlayer(0, config.game.simulation_num_per_move, train=False, weights=model)
    else:
        model = config.data.model_location+player_name
        player = AIPlayer(0, config.game.simulation_num_per_move, train=False, weights=model)
    return player, model
    
def load_player(player, player_name, current, config):
    if player_name == "newest":
        model = sorted(glob.glob(config.data.model_location+"*.h5"))[-1]
        if model != current:
            print("Loading new model: %s" % model)
            player.load_weights(model)
        return model
    else:
        return current
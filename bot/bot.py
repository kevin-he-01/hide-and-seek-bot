from kit import Agent, Team, Direction, apply_direction
import math
import random 
import sys

import traceback, time

# *** Set to True when submitting! ***
submit = False
# Enable local debugging (Ex. exception/error display and logging)
debug = True
# Enable verbose logging, only have effect when debug = True
verbose = False
# Either Team.SEEKER or Team.HIDER depending on which one to let a human control
human_assist = Team.SEEKER

if submit:
    debug = False
    human_assist = None

# Create new agent
agent = Agent()

# initialize agent
agent.initialize()

need_human = human_assist == agent.team

if need_human:
    import human

def main(flog):
    def log(msg):
        if flog != None:
            flog.write('{} <{}>: {}\n'.format(time.asctime(), agent.team.name, msg))
            flog.flush()
    def vlog(msg):
        if verbose:
            log(msg)
    
    while True:
        vlog('Round #{}/200 begins'.format(agent.round_num + 1))
        commands = []
        units = agent.units # list of units you own
        opposingUnits = agent.opposingUnits # list of units on other team that you can see
        game_map = agent.map # the map
        round_num = agent.round_num # the round number
        
        if need_human:
            human.handle(agent, commands)
        else:
            if agent.team == Team.SEEKER:
                # AI Code for seeker goes here

                for _, unit in enumerate(units):
                    # unit.id is id of the unit
                    # unit.x unit.y are its coordinates, unit.distance is distance away from nearest opponent
                    # game_map is the 2D map of what you can see. 
                    # game_map[i][j] returns whats on that tile, 0 = empty, 1 = wall, 
                    # anything else is then the id of a unit which can be yours or the opponents

                    # choose a random direction to move in
                    myDirection = random.choice(list(Direction)).value

                    # apply direction to current unit's position to check if that new position is on the game map
                    (x, y) = apply_direction(unit.x, unit.y, myDirection)
                    if (x < 0 or y < 0 or x >= len(game_map[0]) or y >= len(game_map)):
                        # we do nothing if the new position is not in the map
                        pass
                    else:
                        commands.append(unit.move(myDirection))
                
            else:
                # AI Code for hider goes here
                # hider code, which does nothing, sits tight and hopes it doesn't get 
                # found by seekers
                pass

        vlog('Submitting commands...')
        # submit commands to the engine
        print(','.join(commands))

        vlog('Sending end turn command...')
        # now we end our turn
        agent.end_turn()

        vlog('Waiting for updates from engine...')
        # wait for update from match engine
        agent.update()
        vlog('Updated bot based on response from engine.')

def start(flog):
    if need_human:
        try:
            human.init(agent)
            main(flog)
        finally:
            human.notifyexit()
    else:
        main(flog)

if debug:
    with open('bot-error.log', 'a') as errlog:
        try:
            start(errlog)
        except Exception:
            errlog.write('{}: **** {} Failed during round {} ****\n'.format(time.asctime(), agent.team.name, agent.round_num + 1))
            traceback.print_exc(file=errlog)
            errlog.flush()
else:
    start(None) # TODO maybe add backup strategy/error recovery as random bot or any other known bug free bot instead?
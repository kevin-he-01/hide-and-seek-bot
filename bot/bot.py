# Bot name: clairvoyant
from kit import Agent, Team, Direction, apply_direction, NoPath
import kit

import math
import random 
import sys

import traceback, time, opponent

# *** Set to True when submitting! ***
submit = False
# Enable local debugging (Ex. exception/error display and logging)
debug = True
# Enable verbose logging, only have effect when debug = True
verbose = True
# Either Team.SEEKER or Team.HIDER depending on which one to let a human control
human_assist = None

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

def main(logs):
    def log(msg, unitid=None, level='INFO'):
        for flog in logs:
            identity = agent.team.name if unitid == None else '{} {}'.format(agent.team.name, unitid)
            flog.write('{} [{}] <{}>: {}\n'.format(time.asctime(), level, identity, msg))
            flog.flush()
    def vlog(*args, **kwargs):
        if verbose:
            log(*args, **kwargs, level='DEBUG')
    log('Competition started')
    
    while True:
        vlog('Round #{}/200 begins'.format(agent.round_num))
        commands = []
        units = agent.units # list of units you own
        opposingUnits = agent.opposingUnits # list of units on other team that you can see
        # game_map = agent.map # the map
        # round_num = agent.round_num # the round number
        
        if need_human:
            human.handle(agent, commands)
        else:
            vlog('Visible opponent ids: {}'.format(list(map(lambda unit: unit.id, opposingUnits))))
            if agent.team == Team.SEEKER:
                # AI Code for seeker goes here
                # for _, unit in enumerate(units):
                for unit in units:
                    def ulog(*args, **kwargs):
                        log(*args, **kwargs, unitid=unit.id)
                    def uvlog(*args, **kwargs):
                        vlog(*args, **kwargs, unitid=unit.id)
                    # unit.id is id of the unit
                    # unit.x unit.y are its coordinates, unit.distance is distance away from nearest opponent
                    # game_map is the 2D map of what you can see. 
                    # game_map[i][j] returns whats on that tile, 0 = empty, 1 = wall, 
                    # anything else is then the id of a unit which can be yours or the opponents

                    # # choose a random direction to move in
                    # myDirection = random.choice(list(Direction)).value

                    # # apply direction to current unit's position to check if that new position is on the game map
                    # (x, y) = apply_direction(unit.x, unit.y, myDirection)
                    # if (x < 0 or y < 0 or x >= len(game_map[0]) or y >= len(game_map)):
                    #     # we do nothing if the new position is not in the map
                    #     pass
                    # else:
                    #     commands.append(unit.move(myDirection))
                    closest_dist = math.inf
                    best_moves = [] # Do nothing and stay still
                    dead_hider_ids = []
                    for op in opponent.opponents.values():
                        try:
                            nxdir, dist = agent.pathing(unit.x, unit.y, op.initx, op.inity)
                            uvlog('Distance to opponent {}: {}'.format(op.id, dist))
                            assert len(nxdir) > 0
                            if dist <= 1:
                                ulog('Hider {} should be dead'.format(op.id))
                                dead_hider_ids.append(op.id)
                            else:
                                if dist < closest_dist:
                                    closest_dist = dist
                                    best_moves = nxdir
                        except NoPath:
                            pass
                    for dead_hider_id in dead_hider_ids:
                        del opponent.opponents[dead_hider_id]
                    if len(best_moves) == 0:
                        if opponent:
                            ulog('No path to any hiders!', level='WARN')
                    else:
                        uvlog('Possible next moves: {}'.format(list(map(Direction, best_moves))))
                        my_move = random.choice(best_moves)
                        uvlog('Actually moving toward: {}'.format(Direction(my_move)))
                        commands.append(unit.move(my_move))
                
                if not opponent:
                    log('No opponents left')
            else:
                # AI Code for hider goes here
                # hider code, which does nothing, sits tight and hopes it doesn't get 
                # found by seekers
                pass

        # vlog('Submitting commands...')
        # submit commands to the engine
        print(','.join(commands))

        # vlog('Sending end turn command...')
        # now we end our turn
        agent.end_turn()

        vlog('Round ended. Waiting for updates from engine...')
        # wait for update from match engine
        agent.update()
        vlog('Updated bot based on response from engine.')

def start(logs):
    if need_human:
        try:
            human.init(agent)
            main(logs)
        finally:
            human.notifyexit()
    else:
        main(logs)

if debug:
    with open('common.log', 'a') as common_log, open('{}.log'.format(agent.team.name.lower()), 'a') as specific_log:
        try:
            start([common_log, specific_log])
        except Exception:
            common_log.write('{}: **** {} Failed during round {} ****\n'.format(time.asctime(), agent.team.name, agent.round_num))
            traceback.print_exc(file=common_log)
            common_log.flush()
            raise
else:
    start([]) # TODO maybe add backup strategy/error recovery as random bot or any other known bug free bot instead?
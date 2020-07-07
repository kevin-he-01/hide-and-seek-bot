# Bot name: clairvoyant
from kit import Agent, Team, Direction, apply_direction, NoPath, HiderState, Loop, UnitInfo
from opponent import opponents, Death, Opponent
import opponent as mod_op
import kit, vision

import math
import random 
import sys

import traceback, time

# *** Set to True when submitting! ***
submit = True
# Enable local debugging (Ex. exception/error display and logging)
debug = True
# Enable verbose logging, only have effect when debug = True
verbose = True
# Either Team.SEEKER or Team.HIDER depending on which one to let a human control
human_assist = None
# Random seed for seekers[0] and hiders[1], set to None to randomize
seeds = [2205812789, 3518803024] # Bug seeds

if submit:
    debug = False
    human_assist = None
    seeds = [None, None]

# Create new agent
agent = Agent()

# initialize agent
agent.initialize()

need_human = human_assist == agent.team
seed = seeds[1 if agent.team == Team.HIDER else 0]

if need_human:
    import human

def main(logs):
    global seed
    def log(msg, unitid=None, level='INFO'):
        if level == 'DEBUG' and not verbose:
            return
        for flog in logs:
            identity = agent.team.name if unitid == None else '{} {}'.format(agent.team.name, unitid)
            flog.write('{} [{}] <{}>: {}\n'.format(time.asctime(), level, identity, msg))
            flog.flush()
    def vlog(*args, **kwargs):
        # if verbose:
        log(*args, **kwargs, level='DEBUG')
    if seed == None:
        seed = random.getrandbits(32)
    random.seed(seed)
    log('Competition started with team seed: {}'.format(seed))
    agent.init_log(log, len(logs) > 0)
    agent.post_log_init()
    
    while True:
        vlog('Round #{}/200 begins'.format(agent.round_num))
        commands = []
        units = agent.units # list of units you own
        opposingUnits = agent.opposingUnits # list of units on other team that you can see
        # game_map = agent.map # the map
        round_num = agent.round_num # the round number
        
        vlog('Visible opponent ids: {}'.format(list(map(lambda unit: unit.id, opposingUnits))))
        agent.opponents_update()
        if need_human:
            human.handle(agent, commands)
        else:
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

                    uvlog('Location: {}. R^2 distance to closest opponent {}.'.format((unit.x, unit.y), unit.distance))

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
                    lowest_uncertainty = math.inf
                    best_moves = [] # Do nothing and stay still
                    # primary_target = False # target has primary location, usually in sight
                    # dead_hider_ids = []
                    for op in mod_op.opponents.values():
                        # lastloc = op.get_primary_loc()
                        lastloc = op.lastseen
                        if lastloc != None:
                            goto = lastloc
                        else:
                            # goto = random.choice() # FIXME for seed reasons
                            goto = op.possible_list[0]
                            # ulog('FIXME: no primary locations!', level='WARN')
                            # pass # FIXME use more advanced pathing (Ex. sweep search) in this case
                        uncertainty = op.location_count
                        opx, opy = goto
                        try:
                            nxdir, dist = agent.pathing(unit.x, unit.y, opx, opy)
                            uvlog('Distance to opponent {}: {}'.format(op.id, dist))
                            assert len(nxdir) > 0
                            if dist <= 1:
                                ulog("Hider {} should be dead and shouldn't be on the stage!".format(op.id), level='WARN')
                                # dead_hider_ids.append(op.id)
                            else:
                                if (uncertainty, dist) < (lowest_uncertainty, closest_dist):
                                    closest_dist = dist
                                    lowest_uncertainty = uncertainty
                                    if op.primary_loc != None:
                                        uvlog('Greedily selecting next move from {} by distance'.format(list(map(Direction, nxdir))))
                                        bestmv = None
                                        r2distbest = math.inf
                                        for candidate in nxdir:
                                            cdist = vision.distance_squared(*apply_direction(unit.x, unit.y, candidate), opx, opy)
                                            if cdist < r2distbest:
                                                r2distbest = cdist
                                                bestmv = candidate
                                        best_moves = [bestmv]
                                    else:
                                        best_moves = nxdir
                        except NoPath:
                            ulog('No path to hider ID {}'.format(op.id))
                    # for dead_hider_id in dead_hider_ids:
                    #     del opponents[dead_hider_id]
                    if len(best_moves) == 0:
                        if opponents:
                            ulog('No best next move!', level='WARN')
                    else:
                        uvlog('Possible next moves: {}'.format(list(map(Direction, best_moves))))
                        my_move = random.choice(best_moves)
                        uvlog('Actually moving toward: {}'.format(Direction(my_move)))
                        commands.append(unit.move(my_move))
                
                if not opponents:
                    log('No opponents left')
            else:
                # AI Code for hider goes here
                # hider code, which does nothing, sits tight and hopes it doesn't get 
                # found by seekers
                if debug:
                    agent.debug_distance_map(agent.seeker_map)
                for unit in units:
                    def ulog(*args, **kwargs):
                        log(*args, **kwargs, unitid=unit.id)
                    def uvlog(*args, **kwargs):
                        vlog(*args, **kwargs, unitid=unit.id)
                    myinfo = unit.get_info()
                    hider_state = myinfo.hider_state
                    if hider_state == HiderState.FRESH:
                        loop_candidates = set()
                        viable_target_cells = []
                        my_distance_map = agent.generate_distance_map([(unit.x, unit.y)])
                        for y in range(agent.ydim):
                            for x in range(agent.xdim):
                                if my_distance_map[y][x] != math.inf and my_distance_map[y][x] + 2 <= agent.seeker_map[y][x]:
                                    for loop in agent.loop_index[y][x]:
                                        viable_target_cells.append((x, y))
                                        loop_candidates.add(loop)
                        ulog('Viable loops: {}'.format(list(map(lambda loop: ((loop.x0, loop.y0), (loop.x1, loop.y1)), loop_candidates))))
                        if len(loop_candidates) == 0:
                            ulog('Unable to find a viable loop!', level='WARN')
                        else:
                            for other in units:
                                otherinfo = other.get_info()
                                if len(loop_candidates) > 1:
                                    if other is not unit and otherinfo.hider_loop != None and otherinfo.hider_loop in loop_candidates:
                                        loop_candidates.remove(otherinfo.hider_loop)
                                else:
                                    break
                            hider_loop: Loop = random.choice(list(loop_candidates))
                            myinfo.hider_loop = hider_loop
                            ulog('Chosen loop: {} to {}'.format((hider_loop.x0, hider_loop.y0), (hider_loop.x1, hider_loop.y1)))
                            # for px, py in hider_loop.cell_set:
                            for px, py in viable_target_cells:
                                for other in units:
                                    if other.get_info().hiding_target == (px, py):
                                        break
                                else:
                                    myinfo.hiding_target = (px, py)
                                    break
                            assert myinfo.hiding_target != None
                            ulog('Chosen hiding target {}'.format(myinfo.hiding_target))
                            if myinfo.hiding_target == None:
                                hidex, hidey = viable_target_cells[0]
                                ulog('Have to share hiding target with another unit all @ {}!'.format((hidex, hidey)), level='ERROR')
                                myinfo.hiding_target = (hidex, hidey)
                            ulog('Chosen hiding target: {}'.format(myinfo.hiding_target))
                            hider_state = HiderState.HIDING
                    elif hider_state == HiderState.HIDING:
                        nxdir, dist = agent.pathing(unit.x, unit.y, myinfo.hiding_target[0], myinfo.hiding_target[1])
                        if dist == 0:
                            hider_state = HiderState.CIRCLING
                            ulog('Entered circling state')
                        else:
                            chosendir = random.choice(nxdir)
                            uvlog('Moving with direction {} toward {} to hide'.format(Direction(chosendir), myinfo.hiding_target))
                            commands.append(unit.move(chosendir))
                    if hider_state == HiderState.CIRCLING:
                        uvlog('Circling: seeker distance here: {}'.format(agent.seeker_map[unit.y][unit.x]))
                        maxdist = agent.seeker_map[unit.y][unit.x] # Not moving take precedence
                        mdmove = 8
                        # Greedily choose the lowest distance
                        for dirnum, (dx, dy) in enumerate(kit.direction_deltas):
                            nx = unit.x + dx
                            ny = unit.y + dy
                            if agent.walkable(nx, ny) and (nx, ny) in myinfo.hider_loop.cell_set:
                                newdist = agent.seeker_map[ny][nx]
                                if newdist >= maxdist:
                                    mdmove = dirnum
                                    maxdist = newdist
                        uvlog('Moving toward {} for greatest seeker distance {}'.format(Direction(mdmove), maxdist))
                        commands.append(unit.move(mdmove))
                    unit.get_info().hider_state = hider_state

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
            common_log.write('{}: **** {} Failed during round {} (Seed {}) ****\n'.format(time.asctime(), agent.team.name, agent.round_num, seed))
            traceback.print_exc(file=common_log)
            common_log.flush()
            raise
else:
    start([]) # TODO maybe add backup strategy/error recovery as random bot or any other known bug free bot instead?
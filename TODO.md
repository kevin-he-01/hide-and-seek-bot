# Ranked by implementation readiness
- add vision blocking detection module (by copying code from server using computational geometry/cross product trick)
    - use it on the server to show live result
- implement dirty trick of detecting vertical/horizontal symmetry and thus determining the initial location of opponent with ID = self.ID + 1
- add propensity-based algorithm for finding
    - propensity table: 2D array, 0 = not possible, n > 0: n = number of ways the unit can reach this tile assuming random moves
    - team id assignment, based on minimum maximum distance between any 2 matched units
        - matched unit = 1 our team member to 1 opponent
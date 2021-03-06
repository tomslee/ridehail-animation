#!/usr/bin/python3
"""
A ridehail simulation is composed of vehicles and trips. These atoms
are defined here.
"""
import random
import enum


class Direction(enum.Enum):
    NORTH = [0, 1]
    EAST = [1, 0]
    SOUTH = [0, -1]
    WEST = [-1, 0]


class Equilibration(enum.Enum):
    SUPPLY = "Supply"
    PRICE = "Price"
    NONE = "None"


class TripDistribution(enum.Enum):
    """
    Beta long is mainly center out.
    Beta short is center-focused, origin = distribution
    """
    UNIFORM = 0
    BETA_LONG = 1
    BETA_SHORT = 2
    NORMAL = 3


class TripPhase(enum.Enum):
    INACTIVE = 0
    UNASSIGNED = 1
    WAITING = 2
    RIDING = 3
    COMPLETED = 4
    CANCELLED = 5


class VehiclePhase(enum.Enum):
    """
    Insurance commonly uses these phases
    Phase -1: Not used now: would represent a vehicle not in the system
    Phase  0: App is off. Your personal policy covers you.
    Phase  1: App is on, you're waiting for ride request. ...
    Phase  2: Request accepted, and you're en route to pick up a passenger. ...
    Phase  3: You have passengers in the car.
    """
    # INACTIVE = -1
    IDLE = 0
    DISPATCHED = 1
    WITH_RIDER = 2


class Atom():
    """
    Properties and methods that are common to trips and vehicles
    """
    pass


class Trip(Atom):
    """
    A rider places a request and is taken to a destination
    """
    def __init__(self, i, city, min_trip_distance=0, max_trip_distance=None):
        self.index = i
        self.city = city
        if max_trip_distance is None or max_trip_distance > city.city_size:
            max_trip_distance = city.city_size
        self.origin = self.set_origin()
        self.destination = self.set_destination(self.origin, min_trip_distance,
                                                max_trip_distance)
        self.distance = self.city.distance(self.origin, self.destination)
        self.phase = TripPhase.INACTIVE
        self.phase_time = {}
        for phase in list(TripPhase):
            self.phase_time[phase] = 0

    def set_origin(self):
        return self.city.set_random_location(is_destination=False)

    def set_destination(self,
                        origin,
                        min_trip_distance=0,
                        max_trip_distance=None):
        # Choose a trip_distance:
        if self.city.trip_distribution == TripDistribution.UNIFORM:
            if (max_trip_distance is None
                    or max_trip_distance >= self.city.city_size):
                destination = self.city.set_random_location(
                    is_destination=True)
            else:
                # Impose a minimum and maximum tip distance
                trip_distance = random.randint(min_trip_distance,
                                               max_trip_distance)
                # Choose delta_x
                delta_x = random.randint(0, trip_distance)
                sign_x = random.choice([-1, +1])
                delta_y = trip_distance - delta_x
                sign_y = random.choice([-1, +1])
                destination = [
                    (origin[0] + delta_x * sign_x) % self.city.city_size,
                    (origin[1] + delta_y * sign_y) % self.city.city_size
                ]
        else:
            while True:
                destination = self.city.set_random_location(
                    is_destination=True)
                if (self.city.distance(origin, destination) >=
                        min_trip_distance):
                    break
                if (self.city.distance(origin, destination) <=
                        max_trip_distance):
                    break
        return destination

    def phase_change(self, to_phase=None):
        """
        A trip changes phase from one phase to the next.
        On calling this function, the trip is in phase
        self.phase. It will change to the next phase.
        For now, the "to_phase" argument is used only when trips
        are abandoned, as otherwise the sequence is fixed.
        """
        if not to_phase:
            to_phase = TripPhase((self.phase.value + 1) % len(list(TripPhase)))
        self.phase = to_phase


class Vehicle(Atom):
    """
    A vehicle and its state

    """
    def __init__(self, i, city, idle_vehicles_moving=False, location=[0, 0]):
        """
        Create a vehicle at a random location.
        Grid has edge self.city.city_size, in blocks spaced 1 apart
        """
        self.index = i
        self.city = city
        self.idle_vehicles_moving = idle_vehicles_moving
        self.location = self.city.set_random_location()
        self.direction = random.choice(list(Direction))
        self.phase = VehiclePhase.IDLE
        self.trip_index = None
        self.pickup = []
        self.dropoff = []

    def phase_change(self, to_phase=None, trip=None):
        """
        Vehicle phase change
        In the routine, self.phase is the *from* phase
        """
        if not to_phase:
            # The usual case: move to the next phase in sequence
            to_phase = VehiclePhase(
                (self.phase.value + 1) % len(list(VehiclePhase)))
        if self.phase == VehiclePhase.IDLE:
            # Vehicle is assigned to a new trip
            self.trip_index = trip.index
            self.pickup = trip.origin
            self.dropoff = trip.destination
        elif self.phase == VehiclePhase.DISPATCHED:
            pass
        elif self.phase == VehiclePhase.WITH_RIDER:
            # Vehicle has arrived at the destination and the trip
            # is completed.
            # Clear out information about the now-completed trip
            # from the vehicle's state
            self.trip_index = None
            self.pickup = []
            self.dropoff = []
        self.phase = to_phase

    def update_direction(self):
        """
        Decide which way to turn, and change phase if needed
        """
        original_direction = self.direction
        if self.phase == VehiclePhase.DISPATCHED:
            # For a vehicle on the way to pick up a trip, turn towards the
            # pickup point
            new_direction = self._navigate_towards(self.location, self.pickup)
        elif self.phase == VehiclePhase.WITH_RIDER:
            new_direction = self._navigate_towards(self.location, self.dropoff)
        elif self.phase == VehiclePhase.IDLE:
            if self.idle_vehicles_moving:
                if self.city.trip_distribution in (TripDistribution.BETA_SHORT,
                                                   TripDistribution.BETA_LONG):
                    # Navigate towards the "city center"
                    midpoint = int(self.city.city_size / 2)
                    new_direction = self._navigate_towards(
                        self.location, [midpoint, midpoint])
                else:
                    new_direction = random.choice(list(Direction))
            else:
                new_direction = self.direction
            # No u turns: is_opposite is -1 for opposite,
            # in which case keep on going
            is_opposite = 0
            if new_direction is None:
                is_opposite = -1
            else:
                for i in [0, 1]:
                    is_opposite += (new_direction.value[i] *
                                    self.direction.value[i])
            if is_opposite == -1:
                new_direction = random.choice(list(Direction))
        if not new_direction:
            # arrived at destination (pickup or dropoff)
            new_direction = original_direction
        self.direction = new_direction

    def update_location(self):
        """
        Update the vehicle's location. Continue driving in the same direction
        """
        old_location = self.location.copy()
        if (self.phase == VehiclePhase.IDLE and not self.idle_vehicles_moving):
            # this vehicle does not move
            pass
        elif (self.phase == VehiclePhase.DISPATCHED
              and self.location == self.pickup):
            # the vehicle is at the pickup location:
            # do not move. Usually picking up is handled
            # at the end of the previous block: this
            # code should run only when the vehicle
            # is at the pickup location when called
            pass
        else:
            for i, _ in enumerate(self.location):
                # Handle going off the edge
                self.location[i] = (
                    (old_location[i] + self.direction.value[i]) %
                    self.city.city_size)

    def _navigate_towards(self, current_location, destination):
        """
        At an intersection turn towards a destination
        (perhaps a pickup, perhaps a dropoff).
        The direction is chosen based on the quadrant
        relative to destination
        Values of zero are on the borders
        """
        delta = [current_location[i] - destination[i] for i in (0, 1)]
        quadrant_length = self.city.city_size / 2
        candidate_direction = []
        # go east or west?
        if (delta[0] > 0 and delta[0] < quadrant_length) or (
                delta[0] < 0 and delta[0] <= -quadrant_length):
            candidate_direction.append(Direction.WEST)
        elif delta[0] == 0:
            pass
        else:
            candidate_direction.append(Direction.EAST)
        # go north or south?
        if (delta[1] > 0 and delta[1] < quadrant_length) or (
                delta[1] < 0 and delta[1] <= -quadrant_length):
            candidate_direction.append(Direction.SOUTH)
        elif delta[1] == 0:
            pass
        else:
            candidate_direction.append(Direction.NORTH)
        if len(candidate_direction) > 0:
            direction = random.choice(candidate_direction)
        else:
            direction = None
        return direction


class City():
    """
    Location-specific stuff
    """
    def __init__(self,
                 city_size=10,
                 trip_distribution=TripDistribution.UNIFORM):
        self.city_size = city_size
        self.trip_distribution = trip_distribution

    def set_random_location(self, is_destination=False):
        """
        set a random location in the city
        """
        location = [None, None]
        for i in [0, 1]:
            if self.trip_distribution == TripDistribution.UNIFORM:
                # randint(a, b) returns an integer N: a <= N <= b
                location[i] = random.randint(0, self.city_size - 1)
            elif self.trip_distribution == TripDistribution.NORMAL:
                # triangular takes (low, high, midpoint)
                # betavariate takes (alpha, beta) and returns values in [0, 1]
                # normalvariate takes (mean, sigma)
                pass
            elif self.trip_distribution in (TripDistribution.BETA_SHORT,
                                            TripDistribution.BETA_LONG):
                alpha = 5.0
                beta = alpha
                location[i] = int(
                    random.betavariate(alpha, beta) * self.city_size)
                if (is_destination and
                        self.trip_distribution == TripDistribution.BETA_LONG):
                    location[i] = ((location[i] + int(self.city_size) / 2) %
                                   self.city_size)
        return location

    def distance(self, position_0, position_1, threshold=1000):
        """
        Return the distance from position_0 to position_1
        where position_i - (x,y)
        A return of None if there is no distance
        If the distance is bigger than threshold, just return threshold.
        """
        if position_0 is None or position_1 is None:
            return None
        distance = 0
        for i in (0, 1):
            component = (abs(position_0[i] - position_1[i]))
            component = min(component, self.city_size - component)
            distance += component
            if distance > threshold:
                return distance
        return distance

    def travel_distance(self, origin, direction, destination, threshold=1000):
        """
        Return the number of blocks a vehicle at position "origin" traveling
        in direction "direction" must travel to reach "destination".

        The vehicle is committed to moving in the same direction for
        one move because, in simulation.next_block, update_location
        is called before update_direction.

        If the distance is bigger than threshold, just return threshold.
        """
        if origin == destination:
            travel_distance = 0
        else:
            one_step_position = [
                (origin[i] + direction.value[i]) % self.city_size
                for i in [0, 1]
            ]
            travel_distance = 1 + self.distance(one_step_position, destination,
                                                threshold)
        return travel_distance


class History(str, enum.Enum):
    # Vehicles
    VEHICLE_COUNT = "Vehicle count"
    VEHICLE_TIME = "Vehicle time"
    VEHICLE_P1_TIME = "Vehicle P1 time"
    VEHICLE_P2_TIME = "Vehicle P2 time"
    VEHICLE_P3_TIME = "Vehicle P3 time"
    WAIT_TIME = "Wait time"
    VEHICLE_UTILITY = "Vehicle utility"
    # Requests
    REQUEST_RATE = "Request rate"
    REQUEST_CAPITAL = "Request capital"
    # Trips
    TRIP_COUNT = "Trips"
    TRIP_DISTANCE = "Distance"
    COMPLETED_TRIPS = "Completed trips"
    TRIP_UNASSIGNED_TIME = "Trip unassigned time"
    TRIP_AWAITING_TIME = "Trip awaiting time"
    TRIP_RIDING_TIME = "Trip riding time"
    TRIP_UTILITY = "Trip utility"

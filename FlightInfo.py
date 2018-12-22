class Flight(object):
    def __init__(self):
        self.FlightNumber = None
        self.DepartureTime = None
        self.DepartureAirport = None
        self.ArrivalTime = None
        self.ArrivalAirport = None

class Itinerary(object):
    def __init__(self, duration, price, flights):
        self.Duration = duration
        self.Price = price
        self.Flights = flights

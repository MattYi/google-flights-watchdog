import time
import datetime
import re
import urllib2
from FlightInfo import Flight, Itinerary
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

def main():
    # the master url
    googleFlightUrl = "https://www.google.com/flights/#"

    # a list of airports and airlines (for now hard coded)
    # departures = ["SEA", "YVR", "LAX", "LAS", "ORD", "JFK", "EWR", "YYC"]
    departures = ["SEA"]
    # arrivals = ["PEK", "PVG", "CSX", "CTU", "CKG", "HKG", "TSN", "XIY"]
    arrivals = ["PEK"]
    airlines = ["AS", "AA", "KA", "CX", "HU", "JL", "KE", "EK", "SQ"]

    # departure dates (for now hard coded..)
    away = datetime.datetime(2019, 4, 12)
    back = datetime.datetime(2019, 4, 21)

    driver = webdriver.Chrome()
    driver.implicitly_wait(20)

    results = []

    # for now we search for roundtrip only
    for dep in departures:
        for arv in arrivals:
            argList = []
            # build the url
            depArg = dep + "." + arv + "." + away.strftime("%Y-%m-%d")
            arvArg = arv + "." + dep + "." + back.strftime("%Y-%m-%d")
            argList.append("flt=" + depArg + "*" + arvArg)
            argList.append("c:USD") # currency
            argList.append("e:1") # don't know what this is...
            
            airlineList = ",".join(airlines) # comma separated airlines
            argList.append("a:" + airlineList + "*" + airlineList)

            argList.append("sc:b") # business class
            argList.append("sd:1") # don't know what this is
            argList.append("t:f") # don't know either

            # all above args are separated by semicolons
            request = googleFlightUrl + (";".join(argList))

            # send the request and get results...
            driver.get(request)

            # wait until the page loads
            wait = WebDriverWait(driver, 10)
            wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="flt-app"]/div[2]/main[3]/div[9]/div[1]/div[3]/div[5]/div[3]/ol')))
            
            resHtml = BeautifulSoup(driver.page_source, "html.parser")
            
            # Find the list of results
            resultList = resHtml.find("ol", attrs = {"class": "gws-flights-results__result-list" }) # this only covers the "Best Flights" chart
            counter = 1
            for result in resultList.findAll("li", attrs = {"class": re.compile("gws-flights-results__result-item gws-flights__flex-box") }):
                print counter
                price = extractPrice(result) # price
                duration = extractDuration(result)
                itinerary = extractItinerary(result)

                # click on "Select flight" to proceed to the arrival flight selection page
                # note that this selector only works for "Best flights"
                buttonSelector = "#flt-app > div.gws-flights__flex-column.gws-flights__flex-grow > main.gws-flights__flex-column.gws-flights__active-tab.gws-flights__flights-search > div.gws-flights__flex-grow.gws-flights-results__results.gws-flights__flex-column.gws-flights__scrollbar-padding > div.gws-flights-results__results-container.gws-flights__center-content > div:nth-child(3) > div.gws-flights__flex-grow.gws-flights-results__slice-results-desktop > div.gws-flights-results__best-flights > ol > li:nth-child("
                buttonSelector += str(counter)
                buttonSelector += ") > div > div.gws-flights-widgets-expandablecard__header.gws-flights-results__itinerary-card-header > div.gws-flights-results__itinerary-card-summary.gws-flights-results__result-item-summary.gws-flights__flex-box > div.gws-flights-results__select-header.gws-flights__flex-filler"
                
                driver.find_element_by_css_selector(buttonSelector).click()

                wait = WebDriverWait(driver, 10)
                wait.until(ec.visibility_of_element_located((By.XPATH, '//*[@id="flt-app"]/div[2]/main[3]/div[9]/div[1]/div[3]/div[5]/div[3]/ol')))
                returningHtml = BeautifulSoup(driver.page_source, "html.parser")

                

                driver.execute_script("window.history.go(-1)")  # go back to the departure page

                # add the itinerary to the list
                results.append(Itinerary(duration, price, itinerary))
                counter += 1
    
    # print for now
    counter = 0
    for it in results:
        counter += 1
        print "Itinerary " + str(counter)
        for fl in it.Flights:
            print fl.DepartureAirport + " -> " + fl.ArrivalAirport + " " + fl.DepartureTime + " -> " + fl.ArrivalTime
            print fl.FlightNumber
        print "Total duration: " + it.Duration
        print "Price: " + it.Price
        print ""
        

# extract the flight price from the <li> result node
def extractPrice(liNode):
    priceDiv = liNode.find("div", attrs = {"class": "gws-flights-results__itinerary-price" })
    for element in priceDiv.findAll("jsl"):
        if len(element.findChildren()) == 0 and element.text.strip():
            return element.text.strip()

# extract departure and arrival times from the <li> result node
# def extractTimes(liNode):
#     timeDiv = liNode.find("div", attrs = {"class": re.compile("gws-flights-results__times") })
#     for element in timeDiv.findAll("jsl"):
#         for span in element.findChildren():
#             if len(span.findChildren()) == 0 and span.text.strip():
#                 print span.text.strip()

# extract total duration of the itinerary
def extractDuration(liNode):
    durationDiv = liNode.find("div", attrs = {"class": re.compile("gws-flights-results__duration") })
    return durationDiv.text.strip()

# # extract stops
# def extractStops(liNode):
#     stopsDiv = liNode.find("div", attrs = {"class": re.compile("gws-flights-results__stops") })
#     for element in stopsDiv.findAll("jsl", style_=lambda x: x != 'display:none'):
#         if len(element.findChildren()) == 0 and element.text.strip():
#             print element.text.strip()

# extract each leg
def extractItinerary(liNode):
    legs = []
    legDivs = liNode.findAll("div", attrs = {"class": re.compile("gws-flights-results__leg-details") })

    for leg in legDivs:
        currFlight = Flight()

        # =================== Itinerary ===================
        legItineraryDiv = leg.find("div", attrs = {"class": "gws-flights-results__leg-itinerary" })
        
        # Departure
        depDiv = legItineraryDiv.find("div", attrs = {"class": re.compile("gws-flights-results__leg-departure") })

        # Departure time
        depTimeSpan = depDiv.find("span", attrs = {"aria-label": re.compile("Departure") })
        currFlight.DepartureTime = ''
        for element in depTimeSpan.findAll("span"):
            if len(element.findChildren()) == 0 and element.text.strip():
                currFlight.DepartureTime += element.text.strip() # do this to accommodate '+1'
        
        # Departure airport
        depAirportSpan = depDiv.find("div", attrs = {"aria-label": re.compile("Departs") })
        currFlight.DepartureAirport = depAirportSpan.find("span", attrs = {"class": "gws-flights-results__iata-code"}).text.strip()

        # Arrival
        arrDiv = legItineraryDiv.find("div", attrs = {"class": re.compile("gws-flights-results__leg-arrival") })

        # Arrival time
        arrTimeSpan = arrDiv.find("span", attrs = {"aria-label": re.compile("Arrival") })
        currFlight.ArrivalTime = ''
        for element in arrTimeSpan.findAll("span"):
            if len(element.findChildren()) == 0 and element.text.strip():
                currFlight.ArrivalTime += element.text.strip()  # do this to accommodate '+1'

        # Arrival airport
        arrAirportSpan = arrDiv.find("div", attrs = {"aria-label": re.compile("Arrives") })
        currFlight.ArrivalAirport = arrAirportSpan.find("span", attrs = {"class": "gws-flights-results__iata-code"}).text.strip()

        # =================== Flight ===================
        legFlightDiv = leg.find("div", attrs = {"class": re.compile("gws-flights-results__leg-flight") })
        flightNumberDiv = legFlightDiv.find("div", attrs = {"class": re.compile("gws-flights-results__other-leg-info") })
        currFlight.FlightNumber = ''
        for element in flightNumberDiv.findChildren("span", recursive = False):
            for subElement in element.findAll("span"):
                if len(subElement.findChildren()) == 0 and subElement.text.strip():
                    currFlight.FlightNumber += subElement.text.strip()

        legs.append(currFlight)

    return legs


# entry point..
if __name__ == '__main__':
    main()
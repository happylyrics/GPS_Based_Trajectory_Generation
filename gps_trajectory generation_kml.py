# -*- coding: utf-8 -*-

"""
GPS based path planning
author: happylyrics
"""
# Libraries
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import simplekml

# Parameters
r = 5.0  #ArcRadius[m]
vehicle_velocity = 1.50 #RobotVelocity[m/s]

# Waypoint
waypoint0_lat = 33.841026
waypoint0_lon = 132.762288
waypoint1_lat = 33.841674
waypoint1_lon = 132.762299
waypoint2_lat = 33.841672
waypoint2_lon = 132.763082
waypoint3_lat = 33.842227
waypoint3_lon = 132.763082
waypoint4_lat = 33.842236
waypoint4_lon = 132.762310
waypoint5_lat = 33.841995
waypoint5_lon = 132.762302

# Variable init
count = 0
bak_count = 0
q = 0
mod = 0
bak_mod = 0
offset_x = 0
offset_y = 0
waypoint_x = []
waypoint_y = []
waypoint_xy = []
waypoint_0 = [0,0]
arc_count = 0
vector_12 = []
waypoint_ref = []
waypoint_lat = []
waypoint_lon = []
waypoint_list = []

# Add waypoint list
init_lat = waypoint0_lat
init_lon = waypoint0_lon
for i in range(1000):
    way_lat = 'waypoint'+str(i)+'_lat'
    way_lon = 'waypoint'+str(i)+'_lon'
    try:
        if globals()[way_lat]:
            waypoint_list.append([globals()[way_lat],globals()[way_lon]])
    except KeyError:
        break
print("waypointlist_len",len(waypoint_list))

# KML instance creation
kml = simplekml.Kml()

# Ellipsoid
ELLIPSOID_GRS80 = 1 # GRS80
ELLIPSOID_WGS84 = 2 # WGS84

# Long axis radius and flatness by ellipsoid
GEODETIC_DATUM = {
    ELLIPSOID_GRS80: [
        6378137.0,         # [GRS80]Major axis radius
        1 / 298.257222101, # [GRS80]Oblateness
    ],
    ELLIPSOID_WGS84: [
        6378137.0,         # [WGS84]Major axis radius
        1 / 298.257223563, # [WGS84]Oblateness
    ],
}

# Maximum number of iterations
ITERATION_LIMIT = 1000


def vincenty_inverse(lat1, lon1, lat2, lon2, ellipsoid=None):

    # Return 0.0 if there is no difference
    if math.isclose(lat1, lat2) and math.isclose(lon1, lon2):
        return {
            'distance': 0.0,
            'azimuth1': 0.0,
            'azimuth2': 0.0,
        }

    # Obtain the necessary major axis radius (a) and flatness (??) from the constants and calculate the minor axis radius (b) at the time of calculation
    # If the ellipsoid is not specified, the value of GRS80 is used.
    a, ?? = GEODETIC_DATUM.get(ellipsoid, GEODETIC_DATUM.get(ELLIPSOID_GRS80))
    b = (1 - ??) * a

    ??1 = math.radians(lat1)
    ??2 = math.radians(lat2)
    ??1 = math.radians(lon1)
    ??2 = math.radians(lon2)

    # Modified latitude (latitude on the auxiliary sphere)
    U1 = math.atan((1 - ??) * math.tan(??1))
    U2 = math.atan((1 - ??) * math.tan(??2))

    sinU1 = math.sin(U1)
    sinU2 = math.sin(U2)
    cosU1 = math.cos(U1)
    cosU2 = math.cos(U2)

    # Longitude difference between two points
    L = ??2 - ??1

    # Initialize lambda with L
    ?? = L

    # Iterate the following calculations until ?? converges
    # Set an upper limit on the number of iterations, as convergence may not occur at some locations.
    for i in range(ITERATION_LIMIT):
        sin?? = math.sin(??)
        cos?? = math.cos(??)
        sin?? = math.sqrt((cosU2 * sin??) ** 2 + (cosU1 * sinU2 - sinU1 * cosU2 * cos??) ** 2)
        cos?? = sinU1 * sinU2 + cosU1 * cosU2 * cos??
        ?? = math.atan2(sin??, cos??)
        sin?? = cosU1 * cosU2 * sin?? / sin??
        cos2?? = 1 - sin?? ** 2
        cos2??m = cos?? - 2 * sinU1 * sinU2 / cos2??
        C = ?? / 16 * cos2?? * (4 + ?? * (4 - 3 * cos2??))
        ???? = ??
        ?? = L + (1 - C) * ?? * sin?? * (?? + C * sin?? * (cos2??m + C * cos?? * (-1 + 2 * cos2??m ** 2)))

        # If the deviation is less than .0000000000000001, break
        if abs(?? - ????) <= 1e-12:
            break
    else:
        # Returns None if the calculation does not converge
        return None

    # Once ?? converges to the desired accuracy, the following calculation is performed
    u2 = cos2?? * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    ???? = B * sin?? * (cos2??m + B / 4 * (cos?? * (-1 + 2 * cos2??m ** 2) - B / 6 * cos2??m * (-3 + 4 * sin?? ** 2) * (-3 + 4 * cos2??m ** 2)))

    # Distance on the ellipsoid between two points
    s = b * A * (?? - ????)

    # Azimuth angle at each point
    ??1 = math.atan2(cosU2 * sin??, cosU1 * sinU2 - sinU1 * cosU2 * cos??)
    ??2 = math.atan2(cosU1 * sin??, -sinU1 * cosU2 + cosU1 * sinU2 * cos??) + math.pi

    if ??1 < 0:
        ??1 = ??1 + math.pi * 2

    return {
        'distance': s,           # Distance
        'azimuth1': math.degrees(??1), # Azimuth (start point to end point)
        'azimuth2': math.degrees(??2), # Azimuth (end point to start point)
    }

def vincenty_direct(lat, lon, azimuth, distance, ellipsoid=None):

    # Obtain the necessary major axis radius (a) and flatness (??) from the constants and calculate the minor axis radius (b) at the time of calculation
    # If the ellipsoid is not specified, the value of GRS80 is used.
    a, ?? = GEODETIC_DATUM.get(ellipsoid, GEODETIC_DATUM.get(ELLIPSOID_GRS80))
    b = (1 - ??) * a

    # Convert to radians (except distance)
    ??1 = math.radians(lat)
    ??1 = math.radians(lon)
    ??1 = math.radians(azimuth)
    s = distance

    sin??1 = math.sin(??1)
    cos??1 = math.cos(??1)

    # Modified latitude (latitude on the auxiliary sphere)
    U1 = math.atan((1 - ??) * math.tan(??1))

    sinU1 = math.sin(U1)
    cosU1 = math.cos(U1)
    tanU1 = math.tan(U1)

    ??1 = math.atan2(tanU1, cos??1)
    sin?? = cosU1 * sin??1
    cos2?? = 1 - sin?? ** 2
    u2 = cos2?? * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))

    # Initialize ?? with s/(b*A)
    ?? = s / (b * A)

    # Iterate the following calculations until ?? converges
    # Set an upper limit on the number of iterations, as convergence may not occur at some locations.
    for i in range(ITERATION_LIMIT):
        cos2??m = math.cos(2 * ??1 + ??)
        sin?? = math.sin(??)
        cos?? = math.cos(??)
        ???? = B * sin?? * (cos2??m + B / 4 * (cos?? * (-1 + 2 * cos2??m ** 2) - B / 6 * cos2??m * (-3 + 4 * sin?? ** 2) * (-3 + 4 * cos2??m ** 2)))
        ???? = ??
        ?? = s / (b * A) + ????

        # If the deviation is less than .0000000000000001, break
        if abs(?? - ????) <= 1e-12:
            break
    else:
        # Returns None if the calculation does not converge
        return None

    # Once ?? converges to the desired accuracy, perform the following calculations
    x = sinU1 * sin?? - cosU1 * cos?? * cos??1
    ??2 = math.atan2(sinU1 * cos?? + cosU1 * sin?? * cos??1, (1 - ??) * math.sqrt(sin?? ** 2 + x ** 2))
    ?? = math.atan2(sin?? * sin??1, cosU1 * cos?? - sinU1 * sin?? * cos??1)
    C = ?? / 16 * cos2?? * (4 + ?? * (4 - 3 * cos2??))
    L = ?? - (1 - C) * ?? * sin?? * (?? + C * sin?? * (cos2??m + C * cos?? * (-1 + 2 * cos2??m ** 2)))
    ??2 = L + ??1

    ??2 = math.atan2(sin??, -x) + math.pi

    return {
        'lat': math.degrees(??2),     # Latitude
        'lon': math.degrees(??2),     # Longitude
        'azimuth': math.degrees(??2), # Azimuth
    }

# Main loop
waypoint_len = len(waypoint_list)
incre = 0
while waypoint_len > 1:
    if waypoint_len >= 3:
        waypoint1_lat = waypoint_list[incre+1][0]
        waypoint1_lon = waypoint_list[incre+1][1]
        waypoint2_lat = waypoint_list[incre+2][0]
        waypoint2_lon = waypoint_list[incre+2][1]
        
        # waypoint1 coordinate calculation
        result = vincenty_inverse(waypoint0_lat,waypoint0_lon,waypoint1_lat,waypoint1_lon)
        long1, rad = result["distance"], result["azimuth1"]
        # azimuth -> polar
        rad = math.radians((90 - rad + 360) % 360)
        x1 = long1 * math.cos(rad)
        y1 = long1 * math.sin(rad)
        vector_1 = np.array([x1,y1])

        # waypoint2 coordinate calculation
        result = vincenty_inverse(waypoint0_lat,waypoint0_lon,waypoint2_lat,waypoint2_lon)
        long2, rad2 = result["distance"], result["azimuth1"]
        rad2 = math.radians((90 - rad2 + 360) % 360)
        x2 = long2 * math.cos(rad2)
        y2 = long2 * math.sin(rad2)
        vector_2 = np.array([x2,y2])

        # waypoint1_2 coordinate calculation
        result = vincenty_inverse(waypoint1_lat,waypoint1_lon,waypoint2_lat,waypoint2_lon)
        long12, rad12 = result["distance"], result["azimuth1"]
        rad12 = math.radians((90 - rad12 + 360) % 360)
        x12 = long12 * math.cos(rad12)
        y12 = long12 * math.sin(rad12)
        vector_12 = np.array([x12,y12])

        A = (math.acos((long1**2+long12**2-long2**2)/(2*long1*long12)))*180/math.pi
        b = r * math.tan(math.radians(90-A/2))
        vector_0d = (vector_1) - (b * (vector_1/np.linalg.norm(vector_1)))
        long_0d = np.sqrt(vector_0d[0] ** 2 + vector_0d[1] ** 2)
        vector_p0d2 = (vector_1) + (b * ((vector_2 - vector_1)/np.linalg.norm(vector_2 - vector_1)))
        long_d2p2 = long12 - b
        vector_N = np.array([[0,1],[-1,0]]) @ vector_1
        vector_d1c = (np.sign(np.cross(vector_1,vector_2)) * (vector_N/np.linalg.norm(vector_N)) * r) * -1
        vector_0c = vector_0d - np.sign(np.cross(vector_1,vector_2)) * (vector_N/np.linalg.norm(vector_N)) * r 

        q,mod = divmod(long_0d,vehicle_velocity)
        count = bak_count
        # If q == 0, pass to the next route generation. Otherwise, the route is generated.
        if q != 0:
            for i in range(int(q)):
                waypoint_xy = (vehicle_velocity + (vehicle_velocity * i)) * (vector_1 / (np.linalg.norm(vector_1)))
                waypoint_x.append(waypoint_xy[0]+offset_x)
                waypoint_y.append(waypoint_xy[1]+offset_y)
                plt.plot(waypoint_x[count+i],waypoint_y[count+i],marker='.',markersize="12")
            count = int(count + q)

        vector_d1d2 = vector_p0d2 - vector_0d
        long_d1d2 = np.sqrt((vector_p0d2[0] - vector_0d[0]) ** 2 + (vector_p0d2[1] - vector_0d[1]) ** 2)
        circle_theta = math.acos((r**2+r**2-long_d1d2**2)/(2*r*r)) * (180/math.pi)
        arc_d1d2 = 2 * math.pi * r * (circle_theta/360)
        bak_mod = mod
        q,mod = divmod(arc_d1d2+bak_mod,vehicle_velocity)
        # If q == 0, pass to the next route generation. Otherwise, the route is generated.
        if q != 0:
            for i in range(int(q)):
                theta = (((vehicle_velocity - bak_mod)+vehicle_velocity * i)/ (2 * math.pi * r)) * 360
                al = math.sqrt(r**2+r**2-2*r**2*(math.cos(math.radians(theta))))
                fai = math.acos((al**2+r**2-r**2)/(2*al*r)) * np.sign(np.cross(vector_d1c,vector_d1d2))
                vector_nn = np.array([[math.cos(fai),-1*math.sin(fai)],[math.sin(fai),math.cos(fai)]]) @ vector_d1c
                vector_0circle = vector_0d + ((vector_nn/np.linalg.norm(vector_nn)) * al)
                waypoint_x.append(vector_0circle[0]+offset_x)
                waypoint_y.append(vector_0circle[1]+offset_y)
                plt.plot(waypoint_x[count+i],waypoint_y[count+i],marker='.',markersize="12")
            count = int(count + q)
        # If there are three waypoints, the route is generated until the end. 
        # if there are four or more waypoints, only one point is taken and the next process is performed.
        if waypoint_len == 3:
            #waypoint1to2
            bak_mod = mod
            q,mod = divmod(long_d2p2+bak_mod,vehicle_velocity)
            for i in range(int(q)):
                waypoint_xy = vector_p0d2 + ((vehicle_velocity - bak_mod)+(vehicle_velocity * i)) * (vector_12 / (np.linalg.norm(vector_12)))
                waypoint_x.append(waypoint_xy[0]+offset_x)
                waypoint_y.append(waypoint_xy[1]+offset_y)
                plt.plot(waypoint_x[count+i],waypoint_y[count+i],marker='.',markersize="12")
            count = int(count+q)
            #goal
            waypoint_x.append(x2+offset_x)
            waypoint_y.append(y2+offset_y)
            plt.plot(waypoint_x[count],waypoint_y[count],marker='*',markersize="15")
            waypoint_len -= 1
        else:
            #waypoint1to2
            bak_mod = mod
            waypoint_xy = vector_p0d2 + ((vehicle_velocity - bak_mod)+(vehicle_velocity * 0)) * (vector_12 / (np.linalg.norm(vector_12)))
            waypoint_x.append(waypoint_xy[0]+offset_x)
            waypoint_y.append(waypoint_xy[1]+offset_y)
            plt.plot(waypoint_x[count],waypoint_y[count],marker='.',markersize="12")
            offset_x = waypoint_x[-1]
            offset_y = waypoint_y[-1]
            count = int(count+1)
        for i in range (count-bak_count):
            way_long = math.sqrt(waypoint_x[bak_count+i]**2+waypoint_y[bak_count+i]**2)
            way_rad = math.atan2(waypoint_y[bak_count+i], waypoint_x[bak_count+i])
            degree = (90 - math.degrees(way_rad) + 360) % 360
            # Reference latitude, longitude, angle, and distance
            result = vincenty_direct(init_lat, init_lon, degree, way_long, 1)
            if result:
                waypoint_lat.append(result["lat"])
                waypoint_lon.append(result["lon"])
                waypoint_ref.append([result["lat"],result["lon"]])
        waypoint0_lat = waypoint_lat[-1]
        waypoint0_lon = waypoint_lon[-1]
        bak_count = count
    else:   # When there are two waypoints
        # Waypoint1 coordinate calculation
        waypoint0_lat = waypoint_list[incre][0]
        waypoint0_lon = waypoint_list[incre][1]
        waypoint1_lat = waypoint_list[incre+1][0]
        waypoint1_lon = waypoint_list[incre+1][1]

        result = vincenty_inverse(waypoint0_lat,waypoint0_lon,waypoint1_lat,waypoint1_lon)
        long1, rad = result["distance"], result["azimuth1"]
        rad = math.radians((90 - rad + 360) % 360)
        x1 = long1 * math.cos(rad)
        y1 = long1 * math.sin(rad)
        vector_1 = np.array([x1,y1])

        q,mod = divmod(long1,vehicle_velocity)
        #If q == 0 then error. Otherwise, the route is generated.
        if q != 0:
            for i in range(int(q)):
                waypoint_xy = (vehicle_velocity + (vehicle_velocity * i)) * (vector_1 / (np.linalg.norm(vector_1)))
                waypoint_x.append(waypoint_xy[0])
                waypoint_y.append(waypoint_xy[1])
                plt.plot(waypoint_x[i],waypoint_y[i],marker='.',markersize="12")
            count = int(q)
        else:
            print("Distance to target is not sufficient")
            sys.exit()

        for i in range (count):
            way_long = math.sqrt(waypoint_x[bak_count+i]**2+waypoint_y[bak_count+i]**2)
            way_rad = math.atan2(waypoint_y[bak_count+i], waypoint_x[bak_count+i])
            degree = (90 - math.degrees(way_rad) + 360) % 360
            # Reference latitude, longitude, angle, and distance
            result = vincenty_direct(init_lat, init_lon, degree, way_long, 1)
            if result:
                waypoint_lat.append(result["lat"])
                waypoint_lon.append(result["lon"])
                waypoint_ref.append([result["lat"],result["lon"]])
    waypoint_len -= 1
    incre += 1

print(waypoint_ref)

for i in range(len(waypoint_ref)):
    point = kml.newpoint(coords=[(waypoint_lon[i],waypoint_lat[i])])  # lon, lat
    point.style.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-none.png'
    point.style.labelstyle.scale = 1.0
    kml.save("pathplanning.kml")

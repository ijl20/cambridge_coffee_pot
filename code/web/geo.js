
// *********************************************************************************
// ************* Geometric Functions ***********************************************
// *********************************************************************************

// Return distance in m between positions p1 and p2.
// lat/longs in e.g. p1.lat etc
function get_distance(p1, p2)
{
    var R = 6371000; // Earth's mean radius in meter
    var dLat = rad(p2.lat - p1.lat);
    var dLong = rad(p2.lng - p1.lng);
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                    Math.cos(rad(p1.lat)) * Math.cos(rad(p2.lat)) *
                        Math.sin(dLong / 2) * Math.sin(dLong / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    var d = R * c;
    return d; // returns the distance in meter
};

// return {north: .., south: .., east: .., west: .. } as bounds of array of position
function get_box(position_array)
{
    var box = { north: -90, south: 90, east: -180, west: 180 };
    for (var i=0; i<position_array.length; i++)
    {
        if (position_array[i].lat > box.north) box.north = position_array[i].lat;
        if (position_array[i].lat < box.south) box.south = position_array[i].lat;
        if (position_array[i].lng > box.east) box.east = position_array[i].lng;
        if (position_array[i].lng < box.west) box.west = position_array[i].lng;
    }
    return box;
}

// Return true is position is inside bounding polygon
// http://stackoverflow.com/questions/13950062/checking-if-a-longitude-latitude-coordinate-resides-inside-a-complex-polygon-in
function is_inside(position, bounds_path, box)
{
    //console.log('is_inside '+JSON.stringify(position)+', '+JSON.stringify(bounds_path)+', '+JSON.stringify(box));

    // easy optimization - return false if position is outside bounding rectangle (box)
    if ( position.lat > box.north ||
         position.lat < box.south ||
         position.lng < box.west ||
         position.lng > box.east)
        return false;

    var lastPoint = bounds_path[bounds_path.length - 1];
    var isInside = false;
    var x = position.lng;
    for (var i=0; i<bounds_path.length; i++)
    {
        var point = bounds_path[i];
        var x1 = lastPoint.lng;
        var x2 = point.lng;
        var dx = x2 - x1;

        if (Math.abs(dx) > 180.0)
        {
            // we have, most likely, just jumped the dateline
            // (could do further validation to this effect if needed).  normalise the
            // numbers.
            if (x > 0)
            {
                while (x1 < 0)
                    x1 += 360;
                while (x2 < 0)
                    x2 += 360;
            }
            else
            {
                while (x1 > 0)
                    x1 -= 360;
                while (x2 > 0)
                    x2 -= 360;
            }
            dx = x2 - x1;
        }

        if ((x1 <= x && x2 > x) || (x1 >= x && x2 < x))
        {
            var grad = (point.lat - lastPoint.lat) / dx;
            var intersectAtLat = lastPoint.lat + ((x - x1) * grad);

            if (intersectAtLat > position.lat)
                isInside = !isInside;
        }
        lastPoint = point;
    }

    return isInside;
}


// Bearing in degrees from point A -> B (each as {lat: , lng: })
function get_bearing(A, B)
{
    var a = { lat: rad(A.lat), lng: rad(A.lng) };
    var b = { lat: rad(B.lat), lng: rad(B.lng) };

    var y = Math.sin(b.lng-a.lng) * Math.cos(b.lat);
    var x = Math.cos(a.lat)*Math.sin(b.lat) -
                Math.sin(a.lat)*Math.cos(b.lat)*Math.cos(b.lng-a.lng);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

// Return true if bearing A lies between bearings B1 and B2
// B2 must be CLOCKWISE from B1 i.e. larger if the target zone doesn't include 0
function test_bearing_between(a, b1, b2)
{
    if (b1 > b2) // zone includes 0
    {
        return a > b1 || a < b2;
    }
    return a > b1 && a < b2;
}

// Normalize an angle to >=0 & <360
function angle360(a)
{
    var positive = a >= 0;

    var abs_a = Math.abs(a) % 360;

    return positive ? abs_a : 360 - abs_a;
}

// Bearing of 'outside' bisector of corner from B in line from A->B->C
function get_bisector(A,B,C)
{
    var track_in = get_bearing(A,B);

    var track_out = get_bearing(B,C);

    return get_angle_bisector(track_in, track_out);
}

// As above except for angles instead of points
function get_angle_bisector(track_in, track_out)
{
    var bisector = (track_in + track_out) / 2 + 90;

    var bisector_offset = Math.abs(bisector - track_in);

    if (bisector_offset > 90 && bisector_offset < 270) bisector += 180;

    return angle360(bisector);
}

// http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
// Detect whether lines A->B and C->D intersect
// return { intersect: true/false, position: LatLng (if lines do intersect), progress: 0..1 }
// where 'progress' is how far the intersection is along the A->B path
function get_intersect(line1, line2)
{
    var A = line1[0],
        B = line1[1],
        C = line2[0],
        D = line2[1];

    var s1 = { lat: B.lat - A.lat, lng: B.lng - A.lng };
    var s2 = { lat: D.lat - C.lat, lng: D.lng - C.lng };

    var s = (-s1.lat * (A.lng - C.lng) + s1.lng * (A.lat - C.lat)) /
                (-s2.lng * s1.lat + s1.lng * s2.lat);
    var t = ( s2.lng * (A.lat - C.lat) - s2.lat * (A.lng - C.lng)) /
                (-s2.lng * s1.lat + s1.lng * s2.lat);

    if (s >= 0 && s <= 1 && t >= 0 && t <= 1)
    {
        // lines A->B and C->D intersect
        return { success: true,
                 position: { lat: A.lat + (t * s1.lat),
                             lng: A.lng + (t * s1.lng) },
                 progress: t };
    }

    return { success: false }; // lines don't intersect
}

// Perpendicular distance of point P {lat:, lng:} from a line [A,B]
// where A,B are points
function get_distance_from_line(P, line)
{

    // Prepare some values for the calculation
    var R = 6371000; // Earth's mean radius in meter

    var A = line[0];

    var B = line[1];

    var bearing_AP = get_bearing(A, P);

    var bearing_AB = get_bearing(A, B);

    var bearing_BP = get_bearing(B, P);

    // if point P is 'behind' A wrt to B, then return distance from A
    var angle_BAP = (bearing_AP - bearing_AB + 360) % 360;

    //console.log('angle_BAP',angle_BAP);

    if (angle_BAP > 90 && angle_BAP < 270)
    {
        return get_distance(A,P);
    }

    // if point P is 'behind' B wrt to A, then return distance from B
    var angle_ABP = (180 - bearing_BP + bearing_AB + 360) % 360;

    //console.log('angle_ABP',angle_ABP);

    if (angle_ABP > 90 && angle_ABP < 270)
    {
        return get_distance(B,P);
    }

    // ok, so the point P is somewhere between A and B, so return perpendicular distance

    var distance_AB = get_distance(A, P);

    var d = Math.asin(Math.sin(distance_AB/R)*Math.sin(rad(bearing_AP - bearing_AB))) * R;

    return Math.abs(d);
}

//*********************************************************************************************
//*************** CONVERSION FUNCTIONS, E.G. meters to nautical miles *************************
//*********************************************************************************************

// degrees to radians
function rad(x) {
      return x * Math.PI / 180;
};

// meters to nautical miles
function nm(x)
{
        return x * 0.000539956803;
}

// meters to statute miles
function miles(x)
{
        return x * 0.000621371;
}



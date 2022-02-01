import xml.etree.ElementTree as ET
import os
import time
import datetime
import itertools
import numpy
import uuid
from pyproj.crs import CRS
from pyproj.transformer import Transformer

global FILE
global ns_dict
global counter


def progressBar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)

        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end="")

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    # print()


def guid():
    x = str(uuid.uuid4())
    newstr = x.replace("-", "")
    return ("'" + newstr[:22] + "'")


def create_id():
    global counter
    return "#{}".format(next(counter))


def find_reference_point(l):
    # takes a list of lists as input
    # will return the corner point as a list(point with least x and least y and least z)
    x_list = []
    y_list = []
    z_list = []
    reference_point = []

    for x in l:
        x_list.append(x[0])
        y_list.append(x[1])
        z_list.append(x[2])

    minimum_x = numpy.min(x_list)
    minimum_y = numpy.min(y_list)
    minimum_z = numpy.min(z_list)

    return (minimum_x, minimum_y, minimum_z)


def find_max_point(l):
    # takes a list of lists as input
    # will return a point with maxium values as a list(point with max x and max y and max z)
    x_list = []
    y_list = []
    z_list = []
    max_point = []
    for x in l:
        x_list.append(x[0])
        y_list.append(x[1])
        z_list.append(x[2])

    max_x = numpy.max(x_list)
    max_y = numpy.max(y_list)
    max_z = numpy.max(z_list)

    return (max_x, max_y, max_z)


def move_to_local(reference_point, l):
    # will convert list of points into local coordinates by subtracting the local point value from them
    local_points_list = []
    #tranformed_points = l
    tranformed_points = []
    for point in l:
        tranformed_points.append(transform_coordinates_db(point))

    for point in tranformed_points:
        result = numpy.subtract(point, reference_point)
        local_points_list.append(numpy.ndarray.tolist(result))
    return local_points_list


def get_global_coordinates(x1, y1, z):
    # convert coordinates from EPSG28992 TO WGS84
    in_proj = CRS.from_epsg(25832)  # ETRS89_UTM32
    out_proj = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(in_proj, out_proj)
    x2, y2 = transformer.transform(x1, y1)
    return (x2, y2, z)


def transform_coordinates_db(point_list):
    # convert coordinates from EPSG28992 TO WGS84

    x1 = point_list[0]
    y1 = point_list[1]
    z1 = point_list[2]
    in_proj = CRS.from_epsg(25832)  # ETRS89_UTM32
    out_proj = CRS.from_epsg(5683)  # DB_REF / 3-degree Gauss-Kruger zone 3
    transformer = Transformer.from_crs(in_proj, out_proj)
    x2, y2, z2 = transformer.transform(x1, y1,z1)
    return (x2, y2, z2)


def chunks(l, n):
    # break the list "l" into sub-lists each has the length of "n"
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


def list_to_string(list):
    text = ""
    for el in list:
        text += str(el) + ","
    return text[:-1]


def add_address(building, building_id):
    core = ns_dict.get("ns_citygml")
    xal = "{urn:oasis:names:tc:ciq:xsdschema:xAL:2.0}"

    id_list = []

    text_dict = {
        "CountryName": [create_id(), "empty"],
        "LocalityName": [create_id(), "empty"],
        "ThoroughfareNumber": [create_id(), "Straße unbekannt"],
        "ThoroughfareName": [create_id(), "Gebäude"],
    }

    type_dict = {
        "Locality": [create_id(), "empty"],
        "Thoroughfare": [create_id(), "empty"],
    }

    for tag, tupl in text_dict.items():
        obj = building.find(".//{}{}".format(xal, tag))
        if obj is not None:
            tupl[1] = obj.text.strip()

        id_list.append(tupl[0])
        add_single_value(tupl[0], tag, tupl[1])

    for tag, tupl in type_dict.items():
        obj = building.find(".//{}{}".format(xal, tag))
        if obj is not None:
            value = obj.get("Type")
            if value is not None:
                tupl[1] = value.strip()

        id_list.append(tupl[0])
        add_single_value(tupl[0], tag, value)
    add_pset(id_list, building_id, "Adresse")

    building_name = "{},{}".format(text_dict["ThoroughfareName"][1], text_dict["ThoroughfareNumber"][1])
    return building_name


def add_single_value(id, name, value):
    text = "\n{id} = IFCPROPERTYSINGLEVALUE('{name}',$,IFCTEXT('{value}'),$);"
    text = text.format(id=id, name=name, value=value)
    FILE.write(text)
    pass


def add_attributes(building, building_id):
    global counter

    ns_gen = ns_dict["ns_gen"]
    attribute_id_list = []
    for attribute in building.iterfind('.//{%s}stringAttribute' % ns_gen):
        name = attribute.get("name")
        value_list = attribute.findall('.//{%s}value' % ns_gen)
        value = value_list[0].text

        attribute_id = create_id()
        add_single_value(attribute_id, name, value)
        attribute_id_list.append(attribute_id)

    add_pset(attribute_id_list, building_id, "cityGML Data")


def add_pset(attribute_id_list, building_id, name):
    global counter
    pset_id = "#" + str(next(counter))
    text = "\n{id} = IFCPROPERTYSET({guid},#102,'{name}',$,({attributes}));"
    text = text.format(id=pset_id, guid=guid(), attributes=list_to_string(attribute_id_list), name=name)
    FILE.write(text)

    text = "\n#{id} = IFCRELDEFINESBYPROPERTIES({guid},#102,$,$,({id_2}),{id_3}); "
    text = text.format(id=next(counter), guid=guid(), id_2=building_id, id_3=pset_id)
    FILE.write(text)
    pass


def import_namespace(root):
    ns_dict = {}
    if root.tag == "{http://www.opengis.net/citygml/1.0}CityModel":
        # -- Name spaces
        ns_dict["ns_citygml"] = "http://www.opengis.net/citygml/1.0"
        ns_dict["ns_gml"] = "http://www.opengis.net/gml"
        ns_dict["ns_bldg"] = "http://www.opengis.net/citygml/building/1.0"
        ns_dict["ns_tran"] = "http://www.opengis.net/citygml/transportation/1.0"
        ns_dict["ns_veg"] = "http://www.opengis.net/citygml/vegetation/1.0"
        ns_dict["ns_gen"] = "http://www.opengis.net/citygml/generics/1.0"
        ns_dict["ns_xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        ns_dict["ns_xAL"] = "urn:oasis:names:tc:ciq:xsdschema:xAL:1.0"
        ns_dict["ns_xlink"] = "http://www.w3.org/1999/xlink"
        ns_dict["ns_dem"] = "http://www.opengis.net/citygml/relief/1.0"
        ns_dict["ns_frn"] = "http://www.opengis.net/citygml/cityfurniture/1.0"
        ns_dict["ns_tun"] = "http://www.opengis.net/citygml/tunnel/1.0"
        ns_dict["ns_wtr"] = "http://www.opengis.net/citygml/waterbody/1.0"
        ns_dict["ns_brid"] = "http://www.opengis.net/citygml/bridge/1.0"
        ns_dict["ns_app"] = "http://www.opengis.net/citygml/appearance/1.0"
    # -- Else probably means 2.0
    else:
        # -- Name spaces
        ns_dict["ns_citygml"] = "http://www.opengis.net/citygml/2.0"
        ns_dict["ns_gml"] = "http://www.opengis.net/gml"
        ns_dict["ns_bldg"] = "http://www.opengis.net/citygml/building/2.0"
        ns_dict["ns_tran"] = "http://www.opengis.net/citygml/transportation/2.0"
        ns_dict["ns_veg"] = "http://www.opengis.net/citygml/vegetation/2.0"
        ns_dict["ns_gen"] = "http://www.opengis.net/citygml/generics/2.0"
        ns_dict["ns_xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        ns_dict["ns_xAL"] = "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
        ns_dict["ns_xlink"] = "http://www.w3.org/1999/xlink"
        ns_dict["ns_dem"] = "http://www.opengis.net/citygml/relief/2.0"
        ns_dict["ns_frn"] = "http://www.opengis.net/citygml/cityfurniture/2.0"
        ns_dict["ns_tun"] = "http://www.opengis.net/citygml/tunnel/2.0"
        ns_dict["ns_wtr"] = "http://www.opengis.net/citygml/waterbody/2.0"
        ns_dict["ns_brid"] = "http://www.opengis.net/citygml/bridge/2.0"
        ns_dict["ns_app"] = "http://www.opengis.net/citygml/appearance/2.0"

    ns_dict[None] = ns_dict["ns_citygml"]

    return ns_dict

def write_header(FILE):
    dmy = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(os.path.getmtime(path)))
    # dmys will print the current time in IFC compatible formay
    dmys = "'" + dmy + "'"

    t1 = datetime.datetime(1970, 1, 1)
    t2 = datetime.datetime.now()
    tdif = t2 - t1

    text = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition[CoordinationView_V2.0]'), '2;1');
FILE_NAME('{filename}', {dmys});
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#101 = IFCORGANIZATION ($, 'DB_Netz', 'DB_Netz Abteilung Karlsruhe', $, $); 
#104 = IFCPERSON ($, 'Mellüh', 'Christoph', $, $, $, 'Werkstudent', '99510 Apolda');
#103 = IFCPERSONANDORGANIZATION (#104, #101, $);
#105 = IFCAPPLICATION (#101, 'CityGML2IFC', 'CityGML2IFC', 'CityGML2IFC');
#102 = IFCOWNERHISTORY (#103, #105, .READWRITE., .NOCHANGE., $, $, $,  {creation_date});
#108 = IFCAXIS2PLACEMENT3D (#109, #110, #111);
#109 = IFCCARTESIANPOINT ((0., 0., 0.));
#110 = IFCDIRECTION ((0., 0., 1.)); 
#111 = IFCDIRECTION ((1., 0., 0.)); 
#112 = IFCDIRECTION ((1., 0., 0.)); 
#107 = IFCGEOMETRICREPRESENTATIONCONTEXT ($, 'Model', 3, 1.E-005, #108, #112);
#114 = IFCSIUNIT (*, .LENGTHUNIT., $, .METRE.); 
#113 = IFCUNITASSIGNMENT ((#114));
#115 = IFCMATERIAL('K01-1');
#116 = IFCMATERIAL('K01-2');
#117 = IFCMATERIAL('K01-3');  
#118 = IFCMATERIAL('K01-4');
#119 = IFCLOCALPLACEMENT($,#108);
"""
    text = text.format(filename=FILE.name,
                       dmys=dmys,
                       creation_date = int(tdif.total_seconds()))
    FILE.write(text)

def CityGML2IFC(path, dst,reference_point_db_ref = None):
    global FILE
    global ns_dict
    global counter
    tree = ET.parse(path)
    counter = itertools.count(10000)
    # counter is used to createa a hashtaged unique id with an incremintal value starting from the value given above

    root = tree.getroot()
    # define name spaces

    ns_dict = import_namespace(root)




    cityObjects = []
    buildings = []
    generic = []
    other = []
    # -- Find all instances of cityObjectMember and put them in a list
    for obj in root.iter('{%s}cityObjectMember' % ns_dict["ns_citygml"]):
        cityObjects.append(obj)

    for cityObject in cityObjects:
        # createa a list of different city objects
        for child in list(cityObject):
            if child.tag == '{%s}Building' % ns_dict["ns_bldg"]:
                buildings.append(child)
            elif child.tag == '{%s}GenericCityObject' % ns_dict["ns_gen"]:
                generic.append(child)
            else:
                other.append(child)

    FILE = open(dst, "w", encoding="iso-8859-1")

    # ---------------------------------------------------------------------------------------------------------------------
    # define the ultimate reference point so that all points will have positive/small values
    points_list_complete = []
    pos2 = tree.findall('.//{%s}posList' % ns_dict["ns_gml"])
    for pos in pos2:
        x = ([float(val) for val in (pos.text).strip().split(' ')])
        points_list_complete.append(x)

    reference_point = find_reference_point(points_list_complete)
    reference_point_wgs84 = get_global_coordinates(reference_point[0], reference_point[1], reference_point[2])

    if reference_point_db_ref is None:
        reference_point_db_ref = transform_coordinates_db(reference_point)



    max_point = find_max_point(points_list_complete)
    max_point_wgs84 = get_global_coordinates(max_point[0], max_point[1], max_point[2])
    # ---------------------------------------------------------------------------------------------------------------------
    ifcprojectid = create_id()
    ifcsiteid = create_id()

    wall_id_list = []
    ground_id_list = []
    roof_id_list = []
    floor_id_list = []
    write_header(FILE)
    text = """#120 = IFCCARTESIANPOINT (({x_pos}, {y_pos}, {z_pos}));
#121 = IFCAXIS2PLACEMENT3D(#120,$,$);
#122 = IFCLOCALPLACEMENT($,#121);
#123 = IFCCARTESIANPOINT ((0, 0, 0));
#124 = IFCAXIS2PLACEMENT3D(#123,$,$);
#125 = IFCLOCALPLACEMENT(#122,#124);
{ifcprojectid} = IFCPROJECT ({project_guid}, #102, 'Citygml Import', 'This is File was created by transforming a cityGML', $, $,'ENTWURF', (#107), #113);
{ifcsiteid} = IFCSITE ({site_guid}, #102, 'Studernheim_TRANS', 'Beschreibung Studernheim', 'LandUse', #122, $, $, .ELEMENT.,{max_point},{reference_point}, $, $, $);
#{id_1} = IFCRELAGGREGATES ( {guid_1},#102, $, $, {ifcprojectid}, ({ifcsiteid}));"""
    text = text.format(ifcprojectid=ifcprojectid,
                       ifcsiteid=ifcsiteid,
                       project_guid=guid(),
                       site_guid=guid(),
                       max_point=max_point_wgs84,
                       reference_point=reference_point_wgs84,
                       id_1=next(counter),
                       guid_1=guid(),
                       x_pos=reference_point_db_ref[0],
                       y_pos=reference_point_db_ref[1],
                       z_pos=reference_point_db_ref[2])

    FILE.write(text)

    for building_int, building in enumerate(
            progressBar(buildings, prefix='Progress:', suffix='Complete', length=50, decimals=2)):
        ifcbuildingid = create_id()
        building_name = add_address(building, ifcbuildingid)


        ifcsurfaceid_list = []
        BoundedBy = building.findall('.//{%s}boundedBy' % ns_dict["ns_bldg"])

        for Boundary in BoundedBy:
            # iterate over every boundedby class
            surfaces = Boundary.findall('.//{%s}surfaceMember' % ns_dict["ns_gml"])
            for surface in surfaces:
                ifc_id_list = []
                pl = 0
                pos = surface.find('.//{%s}posList' % ns_dict["ns_gml"])
                points_list = [float(val) for val in (pos.text).strip().split(' ')]
                # points list is the list of the bounding points eg. (5 points for rectangle) every three points have the value of x and y and z
                points_list_chunks = chunks(points_list, 3)
                # reference_point=find_reference_point(points_list_chunks)
                bounding_points = move_to_local(reference_point_db_ref, points_list_chunks)

                for b_points in bounding_points:
                    # iterate over every point in the boundary and create an elemetn from this point and store the id in ifc_id_list
                    ifc_id = create_id()

                    text = "\n{id} = IFCCARTESIANPOINT (({points}));"
                    text = text.format(id=ifc_id, points=str(b_points).strip("[]"))
                    FILE.write(text)

                    ifc_id_list.append(ifc_id)

                ifcpolyloopid = create_id()

                text = "\n{id} = IFCPOLYLOOP (({loop_elements}));"
                text = text.format(id=ifcpolyloopid, loop_elements=",".join(ifc_id_list))
                FILE.write(text)

                ifcfaceouterboundid = create_id()
                text = "\n{ifcfaceouterboundid} = IFCFACEOUTERBOUND ({ifcpolyloopid}, .T.);"
                text = text.format(ifcfaceouterboundid=ifcfaceouterboundid, ifcpolyloopid=ifcpolyloopid)
                FILE.write(text)

                ifcfaceid = create_id()
                text = "\n{ifcfaceid} = IFCFACE (({ifcfaceouterboundid}));"
                text = text.format(ifcfaceid=ifcfaceid, ifcfaceouterboundid=ifcfaceouterboundid)
                FILE.write(text)

                ifcopenshellid = create_id()

                text = "\n{id} = IFCOPENSHELL (({faceid}));"
                text = text.format(id=ifcopenshellid, faceid=ifcfaceid)
                FILE.write(text)

                ifcshellbasedsurfacemodelid = create_id()
                text = "\n{id} = IFCSHELLBASEDSURFACEMODEL (({os_id}));"
                text = text.format(id=ifcshellbasedsurfacemodelid, os_id=ifcopenshellid)
                FILE.write(text)

                ifcshaperepresentationid = create_id()
                text = "\n{id} = IFCSHAPEREPRESENTATION ($,'Body','SurfaceModel',({sh_id}));"
                text = text.format(id=ifcshaperepresentationid, sh_id=ifcshellbasedsurfacemodelid)
                FILE.write(text)

                ifcproductdefiniteshapeid = create_id()
                text = "\n{id} = IFCPRODUCTDEFINITIONSHAPE ($, $, ({sh_id}));"
                text = text.format(id=ifcproductdefiniteshapeid, sh_id=ifcshaperepresentationid)
                FILE.write(text)

                if (Boundary.find('{%s}GroundSurface' % ns_dict["ns_bldg"])):
                    ifcsurfaceid = create_id()
                    text = "\n{id} = IFCSLAB({guid}, $, 'GroundSlab', ' ',$,{pos_id}, {sh_id}, $, .BASESLAB.); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid, pos_id="#125")
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    ground_id_list.append(ifcsurfaceid)

                if (Boundary.find('{%s}FloorSurface' % ns_dict["ns_bldg"])):
                    ifcsurfaceid = create_id()
                    text = "\n{id} = IFCSLAB({guid}, $, 'GroundSlab', ' ',$,{pos_id}, {sh_id}, $, .BASESLAB.); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid, pos_id="#125")
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    floor_id_list.append(ifcsurfaceid)

                if (Boundary.find('{%s}RoofSurface' % ns_dict["ns_bldg"])):
                    ifcsurfaceid = create_id()
                    text = "\n{id} = IFCROOF({guid}, $, 'RoofSlab', ' ',$,{pos_id}, {sh_id}, $, .ROOF.); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid, pos_id="#125")
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    roof_id_list.append(ifcsurfaceid)

                if (Boundary.find('{%s}WallSurface' % ns_dict["ns_bldg"])):
                    ifcsurfaceid = create_id()
                    text = "\n{id} = IFCWALL({guid}, $, 'bldg:WallSurface', ' ',$,{pos_id}, {sh_id}, $); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid, pos_id="#125")
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    wall_id_list.append(ifcsurfaceid)

                if (Boundary.find('{%s}InteriorWallSurface' % ns_dict["ns_bldg"])):
                    ifcsurfaceid = create_id()
                    text = "\n{id} = IFCWALL({guid}, $, 'bldg:WallSurface', ' ',$,{pos_id}, {sh_id}, $); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid, pos_id="#125")
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    wall_id_list.append(ifcsurfaceid)

                if (Boundary.find('{%s}CeilingSurface' % ns_dict["ns_bldg"])):
                    ifcsurfaceid = create_id()
                    text = "\n{id} = IFCCOVERING ({guid}, $, 'CoveringSlab', ' ',$,{pos_id}, {sh_id}, $); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid, pos_id="#125")
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    roof_id_list.append(ifcsurfaceid)

        if (ifcsurfaceid_list):
            text= "\n{id_0} = IFCBUILDING ({guid_0}, #102, '{building_name}', $, $, $, $, $, $, $, $, $);"
            text+= "\n#{id_1} = IFCRELAGGREGATES ( {guid_1},#102, $, $, {site_id}, ({building_id}));"
            text += "\n#{id_2} = IFCRELCONTAINEDINSPATIALSTRUCTURE ({guid_2}, #102, $, $, ({lstring}), {building_id});"
            text = text.format(
                id_0 =ifcbuildingid,
                guid_0 =guid(),
                building_name=building_name,
                id_1=next(counter),
                id_2=next(counter),
                guid_1=guid(),
                guid_2=guid(),
                site_id=ifcsiteid,
                lstring=",".join(ifcsurfaceid_list),
                building_id=ifcbuildingid
            )
            FILE.write(text)

    # Added material when needed by commenting the below back in

    # assign material #115 to all walls
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#115);"
    text = text.format(id=next(counter), guid=guid(), lstring=",".join(wall_id_list))
    FILE.write(text)

    # assign material #116 to all roofs
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#116);"
    text = text.format(id=next(counter), guid=guid(), lstring=",".join(roof_id_list))
    FILE.write(text)

    # assign material #117 to all floors
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#117);"
    text = text.format(id=next(counter), guid=guid(), lstring=",".join(floor_id_list))
    FILE.write(text)

    # assign material #118 to all ground
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#118);"
    text = text.format(id=next(counter), guid=guid(), lstring=",".join(ground_id_list))
    FILE.write(text)

    # pipes work
    for pipe in generic:
        pl = 0
        pos = pipe.findall('.//{%s}posList' % ns_dict["ns_gml"])
        for polygon in pos:
            ifc_id_list = []
            pl = 0
            points_list = [float(val) for val in (polygon.text).strip().split(' ')]
            # points list is the list of the bounding points eg. (5 points for rectangle) every three points have the value of x and y and z
            points_list_chunks = chunks(points_list, 3)
            # reference_point=find_reference_point(points_list_chunks)
            bounding_points = move_to_local(reference_point, points_list_chunks)

            while pl < len(bounding_points):
                # iterate over every point in the boundary and create an elemetn from this point and store the id in ifc_id_list
                ifc_id = "#" + str(next(counter))
                text = "{id} = IFCCARTESIANPOINT (({points}));"
                text = text.format(id=ifc_id, points=str(bounding_points[pl]).strip("[]"))
                FILE.write(text)
                ifc_id_list.append(ifc_id)
                pl = pl + 1
            ifcpolyloopid = "#" + str(next(counter))

            # note; end= is used to identify what tp print after printstatment have ended
            loop_string = ""
            for Element_id in ifc_id_list:
                loop_string += (str((Element_id)).strip("''"))
                loop_string += (",")
                loop_string2 = loop_string[:-1]

            text = "\n{id} = IFCPOLYLOOP (({lstring}));"
            text = text.format(id=ifcpolyloopid, lstring=loop_string2)
            FILE.write(text)
            ifcfaceouterboundid = "#" + str(next(counter))

            text = "\n{id} = IFCFACEOUTERBOUND ({pl_id}, .T.);"
            text = text.format(id=ifcfaceouterboundid, pl_id=ifcpolyloopid)
            FILE.write(text)

            ifcfaceid = "#" + str(next(counter))
            text = "\n{id} = IFCFACE (({fo_id}));"
            text = text.format(id=ifcfaceid, pl_id=ifcfaceouterboundid)
            FILE.write(text)

            ifcopenshellid = "#" + str(next(counter))
            text = "\n{id} = IFCOPENSHELL (({f_id}));"
            text = text.format(id=ifcopenshellid, pl_id=ifcfaceid)
            FILE.write(text)

            ifcshellbasedsurfacemodelid = "#" + str(next(counter))
            text = "\n{id} = IFCSHELLBASEDSURFACEMODEL (({os_id}));"
            text = text.format(id=ifcshellbasedsurfacemodelid, os_id=ifcopenshellid)
            FILE.write(text)

            ifcshaperepresentationid = "#" + str(next(counter))
            text = "\n{id} = IFCSHAPEREPRESENTATION ($,'Body','SurfaceModel',({id_2}));"
            text = text.format(id=ifcshaperepresentationid, id_2=ifcshellbasedsurfacemodelid)
            FILE.write(text)

            ifcproductdefiniteshapeid = "#" + str(next(counter))
            text = "\n{id} = IFCPRODUCTDEFINITIONSHAPE ($, $, ({id_2}));"
            text = text.format(id=ifcproductdefiniteshapeid, id_2=ifcshaperepresentationid)
            FILE.write(text)

            text = "\n#{id} = IFCBUILDINGELEMENTPROXY( {guid},#102,'Test extrude',$,$,#119,{id_2},$,$);"
            text = text.format(id=next(counter), guid=guid(), id_2=ifcproductdefiniteshapeid)
            FILE.write(text)

    text = "\n\nENDSEC;\nEND-ISO-10303-21;\n"
    FILE.write(text)
    FILE.close()


if __name__ == "__main__":
    # path="complete_city_mpdel_with_pipes_reprojected.gml"
    path = "StuKu_UR2_LoD2_Ludwigshafen.gml"
    # path="new.gml"
    # path="1.gml"
    # path="complete_city_mpdel_with_pipes_reprojected.gml"
    # path="small_pipe_reprojected.gml"
    # path="new_ground_solid_removed.gml"
    # path="Ground.gml"
    dst = "Result_with_transform.ifc"

    reference_point = (3454000,5486000,0)
    CityGML2IFC(path, dst,reference_point)

import xml.etree.ElementTree as ET
import os
import time
import itertools
import sys
import numpy
import uuid
from pyproj import Proj, transform

def guid():
    x=str(uuid.uuid4())
    newstr = x.replace("-", "")
    return ("'"+newstr[:22]+"'")


def find_reference_point(l):
    #takes a list of lists as input
    #will return the corner point as a list(point with least x and least y and least z)
    x_list = []
    y_list = []
    z_list = []
    reference_point = []

    for x in l:
        x_list.append(x[0])
    minimum_x = numpy.min(x_list)
    reference_point.append(minimum_x)
    for x in l:
        y_list.append(x[1])
    minimum_y = numpy.min(y_list)
    reference_point.append(minimum_y)
    for x in l:
        z_list.append(x[2])
    minimum_z = numpy.min(z_list)
    reference_point.append(minimum_z)
    #return (tuple(reference_point))
    return (minimum_x,minimum_y,minimum_z)

def find_max_point(l):
    #takes a list of lists as input
    #will return a point with maxium values as a list(point with max x and max y and max z)
    x_list = []
    y_list = []
    z_list = []
    max_point = []
    for x in l:
        x_list.append(x[0])
    max_x = numpy.max(x_list)
    max_point.append(max_x)
    for x in l:
        y_list.append(x[1])
    max_y = numpy.max(y_list)
    max_point.append(max_y)
    for x in l:
        z_list.append(x[2])
    max_z = numpy.max(z_list)
    max_point.append(max_z)
    #return (tuple(max_point))
    return (max_x,max_y,max_z)

def move_to_local(local_pont, l):
    #will convert list of points into local coordinates by subtracting the local point value from them
    local_points_list=[]
    for x in l:
        result = numpy.subtract(x, local_pont)
        local_points_list.append(numpy.ndarray.tolist(result))
    return local_points_list

def from_EPSG28992_TO_WGS84(x1,y1,z):
    # convert coordinates from EPSG28992 TO WGS84
    inProj = Proj(init='epsg:28992')
    outProj = Proj(init='epsg:4326')
    x2,y2 = transform(inProj,outProj,x1,y1)
    return (x2,y2,z)

def chunks(l, n):
    #break the list "l" into sub-lists each has the length of "n"
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]

def CityGML2IFC(path,dst):
    tree = ET.parse(path)
    counter = itertools.count(1000)
    #counter is used to createa a hashtaged unique id with an incremintal value starting from the value given above

    root = tree.getroot()
    #define name spaces
    if root.tag == "{http://www.opengis.net/citygml/1.0}CityModel":
        # -- Name spaces
        ns_citygml = "http://www.opengis.net/citygml/1.0"
        ns_gml = "http://www.opengis.net/gml"
        ns_bldg = "http://www.opengis.net/citygml/building/1.0"
        ns_tran = "http://www.opengis.net/citygml/transportation/1.0"
        ns_veg = "http://www.opengis.net/citygml/vegetation/1.0"
        ns_gen = "http://www.opengis.net/citygml/generics/1.0"
        ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
        ns_xAL = "urn:oasis:names:tc:ciq:xsdschema:xAL:1.0"
        ns_xlink = "http://www.w3.org/1999/xlink"
        ns_dem = "http://www.opengis.net/citygml/relief/1.0"
        ns_frn = "http://www.opengis.net/citygml/cityfurniture/1.0"
        ns_tun = "http://www.opengis.net/citygml/tunnel/1.0"
        ns_wtr = "http://www.opengis.net/citygml/waterbody/1.0"
        ns_brid = "http://www.opengis.net/citygml/bridge/1.0"
        ns_app = "http://www.opengis.net/citygml/appearance/1.0"
    # -- Else probably means 2.0
    else:
        # -- Name spaces
        ns_citygml = "http://www.opengis.net/citygml/2.0"
        ns_gml = "http://www.opengis.net/gml"
        ns_bldg = "http://www.opengis.net/citygml/building/2.0"
        ns_tran = "http://www.opengis.net/citygml/transportation/2.0"
        ns_veg = "http://www.opengis.net/citygml/vegetation/2.0"
        ns_gen = "http://www.opengis.net/citygml/generics/2.0"
        ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
        ns_xAL = "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
        ns_xlink = "http://www.w3.org/1999/xlink"
        ns_dem = "http://www.opengis.net/citygml/relief/2.0"
        ns_frn = "http://www.opengis.net/citygml/cityfurniture/2.0"
        ns_tun = "http://www.opengis.net/citygml/tunnel/2.0"
        ns_wtr = "http://www.opengis.net/citygml/waterbody/2.0"
        ns_brid = "http://www.opengis.net/citygml/bridge/2.0"
        ns_app = "http://www.opengis.net/citygml/appearance/2.0"

    nsmap = {
            None : ns_citygml,
            'gml': ns_gml,
            'bldg': ns_bldg,
            'xsi' : ns_xsi,
            'xAL' : ns_xAL,
            'xlink' : ns_xlink,
            'dem' : ns_dem
        }


    dmy=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(os.path.getmtime(path)))
    #dmys will print the current time in IFC compatible formay
    dmys="'"+dmy+"'"

    cityObjects = []
    buildings = []
    generic=[]
    other = []
    #-- Find all instances of cityObjectMember and put them in a list
    for obj in root.getiterator('{%s}cityObjectMember'% ns_citygml):
        cityObjects.append(obj)


    for cityObject in cityObjects:
    #createa a list iof different city objects
        for child in cityObject.getchildren():
            if child.tag == '{%s}Building' %ns_bldg:
                buildings.append(child)
            elif child.tag == '{%s}GenericCityObject' %ns_gen:
                generic.append(child)
            else :
                other.append(child)


    i=0
    FILE = open(dst,"w")
    sys.stdout = FILE
    #sys.stdout = FILE means that every print statment will be saved instead in the file
#---------------------------------------------------------------------------------------------------------------------
    #define the ultimate reference point so that all points will have positive/small values
    points_list_complete = []
    pos2 = tree.findall('.//{%s}posList' % ns_gml)
    for pos in pos2:
        x = ([float(val) for val in (pos.text).strip().split(' ')])
        #points_list_complete.append((x)[:-3])
        points_list_complete.append(x)
    reference_point=find_reference_point(points_list_complete)
    reference_point_wgs84=from_EPSG28992_TO_WGS84(reference_point[0],reference_point[1],reference_point[2])
    max_point=find_max_point(points_list_complete)
    max_point_wgs84=from_EPSG28992_TO_WGS84(max_point[0],max_point[1],max_point[2])
# ---------------------------------------------------------------------------------------------------------------------
    ifcprojectid="#"+str(next(counter))
    ifcsiteid="#"+str(next(counter))
    wall_id_list=[]
    ground_id_list=[]
    roof_id_list=[]
    floor_id_list=[]
    print("\nISO-10303-21;" 
    "\nHEADER;" 
    "\nFILE_DESCRIPTION(('ViewDefinition[CoordinationView_V2.0]'), '2;1');"
    "\nFILE_NAME (","'",(os.path.basename(path)),"'",",",dmys,");" 
    "\nFILE_SCHEMA (('IFC2X3'));" 
    "\nENDSEC;" 
    "\n\nDATA;"
    "\n#101 = IFCORGANIZATION ($, 'MSC_Geomatics', 'TU_Delft', $, $);" 
    "\n#104 = IFCPERSON ($, 'Nebras_salheb', 'TU_Delft', $, $, $, $, $);" 
    "\n#103 = IFCPERSONANDORGANIZATION (#104, #101, $);" 
    "\n#105 = IFCAPPLICATION (#101, 'CityGML2IFC', 'CityGML2IFC', 'CityGML2IFC');" 
    "\n#102 = IFCOWNERHISTORY (#103, #105, .READWRITE., .NOCHANGE., $, $, $, 1528899117);" 
    "\n#109 = IFCCARTESIANPOINT ((0., 0., 0.));" 
    "\n#110 = IFCDIRECTION ((0., 0., 1.));" 
    "\n#111 = IFCDIRECTION ((1., 0., 0.));" 
    "\n#108 = IFCAXIS2PLACEMENT3D (#109, #110, #111);" 
    "\n#112 = IFCDIRECTION ((1., 0., 0.));" 
    "\n#107 = IFCGEOMETRICREPRESENTATIONCONTEXT ($, 'Model', 3, 1.E-005, #108, #112);" 
    "\n#114 = IFCSIUNIT (*, .LENGTHUNIT., $, .METRE.);" 
    "\n#113 = IFCUNITASSIGNMENT ((#114));"
    "\n#115= IFCMATERIAL('K01-1');"
    "\n#116= IFCMATERIAL('K01-2');"
    "\n#117= IFCMATERIAL('K01-3');"    
    "\n#118= IFCMATERIAL('K01-4');"
    "\n#119=IFCLOCALPLACEMENT($,#108);"
    "\n" ,ifcprojectid, " = IFCPROJECT (",guid(),", #102, 'core:CityModel', '', $, $, $, (#107), #113);"  
    "\n",ifcsiteid," = IFCSITE (",guid(),", #102, 'Rotterdam', 'Description of Default Site Rotterdam', 'LandUse', $, $, $, .ELEMENT.,""",max_point_wgs84,",",reference_point_wgs84,", $, $, $);")

    for building in buildings:
        ifcbuildingid = "#" + str(next(counter))
        print(ifcbuildingid," = IFCBUILDING (",guid(),", #102, 'bldg:Building', $, $, $, $, $, $, $, $, $);")
        ifcsurfaceid_list=[]
        BoundedBy=building.findall('.//{%s}boundedBy' %ns_bldg)
        for Boundary in BoundedBy:
        #iterate over every boundedby class
            surfaces=Boundary.findall('.//{%s}surfaceMember' %ns_gml)
            for surface in surfaces:
                ifc_id_list=[]
                pl=0
                pos=surface.find('.//{%s}posList' %ns_gml)
                points_list= [float(val) for val in (pos.text).strip().split(' ')]
                #points list is the list of the bounding points eg. (5 points for rectangle) every three points have the value of x and y and z
                points_list_chunks=chunks(points_list,3)
                #reference_point=find_reference_point(points_list_chunks)
                bounding_points=move_to_local(reference_point,points_list_chunks)

                while pl<len(bounding_points):
                #iterate over every point in the boundary and create an elemetn from this point and store the id in ifc_id_list
                    ifc_id="#"+str(next(counter))
                    print((ifc_id)," = IFCCARTESIANPOINT ((",(str(bounding_points [pl])).strip("[]"),"));")
                    ifc_id_list.append(ifc_id)
                    pl=pl+1
                ifcpolyloopid="#"+str(next(counter))
                print(ifcpolyloopid," = IFCPOLYLOOP ((", end=' ')
                #note; end= is used to identify what tp print after printstatment have ended
                loop_string = ""
                for Element_id in ifc_id_list:
                    loop_string += (str((Element_id)).strip("''"))
                    loop_string += (",")
                    loop_string2 = loop_string[:-1]
                print(loop_string2, "));")

                ifcfaceouterboundid="#"+str(next(counter))
                print(ifcfaceouterboundid," = IFCFACEOUTERBOUND (",ifcpolyloopid,", .T.);")

                ifcfaceid="#"+str(next(counter))
                print(ifcfaceid," = IFCFACE ((",ifcfaceouterboundid,"));")

                ifcopenshellid="#"+str(next(counter))
                print(ifcopenshellid," = IFCOPENSHELL ((",ifcfaceid,"));")

                ifcshellbasedsurfacemodelid="#"+str(next(counter))
                print(ifcshellbasedsurfacemodelid," = IFCSHELLBASEDSURFACEMODEL ((",ifcopenshellid,"));")

                ifcshaperepresentationid="#"+str(next(counter))
                print(ifcshaperepresentationid," = IFCSHAPEREPRESENTATION ($,'Body','SurfaceModel',(",ifcshellbasedsurfacemodelid,"));")

                ifcproductdefiniteshapeid="#"+str(next(counter))
                print(ifcproductdefiniteshapeid," = IFCPRODUCTDEFINITIONSHAPE ($, $, (",ifcshaperepresentationid,"));")


                if(Boundary.find('{%s}GroundSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    print(ifcsurfaceid," = IFCSLAB (",guid(),", $,'GroundSlab',' ',$,$,",ifcproductdefiniteshapeid,",$,.BASESLAB.);")
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    ground_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}FloorSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    print(ifcsurfaceid," = IFCSLAB (",guid(),", $,'GroundSlab',' ',$,$,",ifcproductdefiniteshapeid,",$,.BASESLAB.);")
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    floor_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}RoofSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    print(ifcsurfaceid," = IFCROOF (",guid(),", $,'RoofSlab',' ',$,$,",ifcproductdefiniteshapeid,",$,.ROOF.);")
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    roof_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}WallSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    print(ifcsurfaceid," = IFCWALL (", guid(),", $,'bldg:WallSurface',' ',$,$,",ifcproductdefiniteshapeid,",$);")
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    wall_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}InteriorWallSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    print(ifcsurfaceid," = IFCWALL (",guid(),", $,'bldg:WallSurface',' ',$,$,",ifcproductdefiniteshapeid,",$);")
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    wall_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}CeilingSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    print(ifcsurfaceid," = IFCCovering (",guid(),", $,'CoveringSlab',' ',$,$,",ifcproductdefiniteshapeid,",$,$);")
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    roof_id_list.append(ifcsurfaceid)

        if (ifcsurfaceid_list):
            print("#"+str(next(counter))," = IFCRELAGGREGATES (",guid(),", #102, $, $, ",ifcprojectid,", (", ifcbuildingid,"));")
            print("#"+str(next(counter))," = IFCRELCONTAINEDINSPATIALSTRUCTURE (",guid(),", #102, $, $, (", end=' ')
            loop_string = ""
            for Element_id in ifcsurfaceid_list:
                loop_string += (str((Element_id)).strip("''"))
                loop_string += (",")
                loop_string2 = loop_string[:-1]
            print(loop_string2, "),",ifcbuildingid,");")

#Added material when needed by commenting the below back in

        #assign material #115 to all walls
        print("#"+str(next(counter))," = IFCRELASSOCIATESMATERIAL (",guid(),",#102,$,$,(", end=' ')
        loop_string = ""
        for Element_id in wall_id_list:
            loop_string += (str((Element_id)).strip("''"))
            loop_string += (",")
            loop_string2 = loop_string[:-1]
        print(loop_string2, "),#115);")

        #assign material #116 to all roofs
        print("#"+str(next(counter))," = IFCRELASSOCIATESMATERIAL (",guid(),",#102,$,$,(", end=' ')
        loop_string = ""
        for Element_id in roof_id_list:
            loop_string += (str((Element_id)).strip("''"))
            loop_string += (",")
            loop_string2 = loop_string[:-1]
        print(loop_string2, "),#116);")

        #assign material #117 to all floors
        print("#"+str(next(counter))," = IFCRELASSOCIATESMATERIAL (",guid(),",#102,$,$,(", end=' ')
        loop_string = ""
        for Element_id in floor_id_list:
            loop_string += (str((Element_id)).strip("''"))
            loop_string += (",")
            loop_string2 = loop_string[:-1]
        print(loop_string2, "),#117);")

        #assign material #118 to all ground
        print("#"+str(next(counter))," = IFCRELASSOCIATESMATERIAL (",guid(),",#102,$,$,(", end=' ')
        loop_string = ""
        for Element_id in ground_id_list:
            loop_string += (str((Element_id)).strip("''"))
            loop_string += (",")
            loop_string2 = loop_string[:-1]
        print(loop_string2, "),#118);")

    #pipes work
    for pipe in generic:
        pl = 0
        pos = pipe.findall('.//{%s}posList' % ns_gml)
        for polygon in pos:
            ifc_id_list=[]
            pl=0
            points_list= [float(val) for val in (polygon.text).strip().split(' ')]
            #points list is the list of the bounding points eg. (5 points for rectangle) every three points have the value of x and y and z
            points_list_chunks=chunks(points_list,3)
            #reference_point=find_reference_point(points_list_chunks)
            bounding_points=move_to_local(reference_point,points_list_chunks)

            while pl<len(bounding_points):
            #iterate over every point in the boundary and create an elemetn from this point and store the id in ifc_id_list
                ifc_id="#"+str(next(counter))
                print((ifc_id)," = IFCCARTESIANPOINT ((",(str(bounding_points [pl])).strip("[]"),"));")
                ifc_id_list.append(ifc_id)
                pl=pl+1
            ifcpolyloopid="#"+str(next(counter))
            print(ifcpolyloopid," = IFCPOLYLOOP ((", end=' ')
            #note; end= is used to identify what tp print after printstatment have ended
            loop_string = ""
            for Element_id in ifc_id_list:
                loop_string += (str((Element_id)).strip("''"))
                loop_string += (",")
                loop_string2 = loop_string[:-1]
            print(loop_string2, "));")

            ifcfaceouterboundid="#"+str(next(counter))
            print(ifcfaceouterboundid," = IFCFACEOUTERBOUND (",ifcpolyloopid,", .T.);")

            ifcfaceid="#"+str(next(counter))
            print(ifcfaceid," = IFCFACE ((",ifcfaceouterboundid,"));")

            ifcopenshellid="#"+str(next(counter))
            print(ifcopenshellid," = IFCOPENSHELL ((",ifcfaceid,"));")

            ifcshellbasedsurfacemodelid="#"+str(next(counter))
            print(ifcshellbasedsurfacemodelid," = IFCSHELLBASEDSURFACEMODEL ((",ifcopenshellid,"));")

            ifcshaperepresentationid="#"+str(next(counter))
            print(ifcshaperepresentationid," = IFCSHAPEREPRESENTATION ($,'Body','SurfaceModel',(",ifcshellbasedsurfacemodelid,"));")

            ifcproductdefiniteshapeid="#"+str(next(counter))
            print(ifcproductdefiniteshapeid," = IFCPRODUCTDEFINITIONSHAPE ($, $, (",ifcshaperepresentationid,"));")

            print("#" + str(next(counter)),"=IFCBUILDINGELEMENTPROXY(",guid(),",#102,'Test extrude',$,$,#119,",ifcproductdefiniteshapeid,",$,$);")
    print("\n"
    "\nENDSEC;"
    "\nEND-ISO-10303-21;")

    FILE.write("")
    FILE.close()

#path="complete_city_mpdel_with_pipes_reprojected.gml"
#path="Source.gml"
#path="new.gml"
path="1.gml"
#path="complete_city_mpdel_with_pipes_reprojected.gml"
#path="small_pipe_reprojected.gml"
#path="new_ground_solid_removed.gml"
#path="Ground.gml"
dst="Result.ifc"

CityGML2IFC(path,dst)

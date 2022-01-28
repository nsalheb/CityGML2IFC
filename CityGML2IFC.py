import xml.etree.ElementTree as ET
import os
import time
import itertools
import sys
import numpy
import uuid
from pyproj.crs import CRS
from pyproj.transformer import Transformer

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
    in_proj = CRS.from_epsg(4258)
    out_proj = CRS.from_epsg(5683)
    transformer = Transformer.from_crs(in_proj,out_proj)
    x2,y2 = transformer.transform(x1,y1)
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
    for obj in root.iter('{%s}cityObjectMember'% ns_citygml):
        cityObjects.append(obj)


    for cityObject in cityObjects:
    #createa a list of different city objects
        for child in list(cityObject):
            if child.tag == '{%s}Building' %ns_bldg:
                buildings.append(child)
            elif child.tag == '{%s}GenericCityObject' %ns_gen:
                generic.append(child)
            else :
                other.append(child)


    i=0
    FILE = open(dst,"w")
    #sys.stdout = FILE
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


    text = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition[CoordinationView_V2.0]'), '2;1');
FILE_NAME ('{filename}',{dmys});
FILE_SCHEMA (('IFC2X3'));
ENDSEC;
DATA;
#101 = IFCORGANIZATION ($, 'MSC_Geomatics', 'TU_Delft', $, $); 
#104 = IFCPERSON ($, 'Nebras_salheb', 'TU_Delft', $, $, $, $, $);
#103 = IFCPERSONANDORGANIZATION (#104, #101, $);" 
#105 = IFCAPPLICATION (#101, 'CityGML2IFC', 'CityGML2IFC', 'CityGML2IFC');
#102 = IFCOWNERHISTORY (#103, #105, .READWRITE., .NOCHANGE., $, $, $, 1528899117);
#109 = IFCCARTESIANPOINT ((0., 0., 0.));
#110 = IFCDIRECTION ((0., 0., 1.)); 
#111 = IFCDIRECTION ((1., 0., 0.)); 
#108 = IFCAXIS2PLACEMENT3D (#109, #110, #111);
#112 = IFCDIRECTION ((1., 0., 0.)); 
#107 = IFCGEOMETRICREPRESENTATIONCONTEXT ($, 'Model', 3, 1.E-005, #108, #112);
#114 = IFCSIUNIT (*, .LENGTHUNIT., $, .METRE.); 
#113 = IFCUNITASSIGNMENT ((#114));
#115= IFCMATERIAL('K01-1');
#116= IFCMATERIAL('K01-2');
#117= IFCMATERIAL('K01-3');  
#118= IFCMATERIAL('K01-4');
#119=IFCLOCALPLACEMENT($,#108);
{ifcprojectid} = IFCPROJECT ('{project_guid}', #102, 'core:CityModel', '', $, $, $, (#107), #113);
{ifcsiteid} = IFCSITE ('{site_guid}', #102, 'Apolda', 'Glockenstadt Apolda', 'LandUse', $, $, $, .ELEMENT.,{max_point},{reference_point}, $, $, $);"""
    text = text.format(filename= os.path.basename(path),dmys=dmys,ifcprojectid=ifcprojectid,ifcsiteid=ifcsiteid,project_guid=guid(),site_guid=guid(),max_point=max_point_wgs84,reference_point=reference_point_wgs84)
    FILE.write(text)


    for building_int,building in enumerate(buildings):
        ifcbuildingid = "#" + str(next(counter))

        text = "\n{id} = IFCBUILDING ({guid}, #102, 'Building {i}', $, $, $, $, $, $, $, $, $);"
        text = text.format(id = ifcbuildingid,guid = guid(),i = building_int)
        FILE.write(text)

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

                    text = "\n{id} = IFCCARTESIANPOINT (({points}));"
                    text = text.format(id = ifc_id,points = str(bounding_points [pl]).strip("[]"))
                    FILE.write(text)

                    ifc_id_list.append(ifc_id)
                    pl=pl+1
                ifcpolyloopid="#"+str(next(counter))




                #print(ifcpolyloopid," = IFCPOLYLOOP ((", end=' ')
                #note; end= is used to identify what tp print after printstatment have ended
                loop_string = ""
                for Element_id in ifc_id_list:
                    loop_string += (str((Element_id)).strip("''"))
                    loop_string += (",")
                    loop_string2 = loop_string[:-1]
                #print(loop_string2, "));")
                text = "\n{id} = IFCPOLYLOOP (({loop}));"
                text = text.format(id = ifcpolyloopid,loop = loop_string2)
                FILE.write(text)
                ifcfaceouterboundid="#"+str(next(counter))
                text = "\n{ifcfaceouterboundid} = IFCFACEOUTERBOUND ({ifcpolyloopid}, .T.);"
                text = text.format(ifcfaceouterboundid=ifcfaceouterboundid,ifcpolyloopid = ifcpolyloopid)
                FILE.write(text)
                #print(ifcfaceouterboundid," = IFCFACEOUTERBOUND (",ifcpolyloopid,", .T.);")

                ifcfaceid="#"+str(next(counter))
                text = "\n{ifcfaceid} = IFCFACE (({ifcfaceouterboundid}));"
                text = text.format(ifcfaceid=ifcfaceid,ifcfaceouterboundid=ifcfaceouterboundid)
                FILE.write(text)

                ifcopenshellid="#"+str(next(counter))

                text = "\n{id} = IFCOPENSHELL (({faceid}));"
                text = text.format(id = ifcopenshellid,faceid = ifcfaceid)
                FILE.write(text)

                ifcshellbasedsurfacemodelid="#"+str(next(counter))
                text = "\n{id} = IFCSHELLBASEDSURFACEMODEL (({os_id}));"
                text = text.format(id = ifcshellbasedsurfacemodelid,os_id = ifcopenshellid)
                FILE.write(text)

                ifcshaperepresentationid="#"+str(next(counter))
                text = "\n{id} = IFCSHAPEREPRESENTATION ($,'Body','SurfaceModel',({sh_id}));"
                text = text.format(id=ifcshaperepresentationid, sh_id=ifcshellbasedsurfacemodelid)
                FILE.write(text)

                ifcproductdefiniteshapeid="#"+str(next(counter))
                text = "\n{id} = IFCPRODUCTDEFINITIONSHAPE ($, $, ({sh_id}));"
                text = text.format(id=ifcproductdefiniteshapeid, sh_id=ifcshaperepresentationid)
                FILE.write(text)


                if(Boundary.find('{%s}GroundSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    text = "\n{id} = IFCSLAB({guid}, $, 'GroundSlab', ' ',$,$, {sh_id}, $, .BASESLAB.); "
                    text = text.format(id = ifcsurfaceid,guid = guid(),sh_id = ifcproductdefiniteshapeid)
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    ground_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}FloorSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    text = "\n{id} = IFCSLAB({guid}, $, 'GroundSlab', ' ',$,$, {sh_id}, $, .BASESLAB.); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid)
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    floor_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}RoofSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    text = "\n{id} = IFCROOF({guid}, $, 'RoofSlab', ' ',$,$, {sh_id}, $, .ROOF.); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid)
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    roof_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}WallSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    text = "\n{id} = IFCWALL({guid}, $, 'bldg:WallSurface', ' ',$,$, {sh_id}, $,); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid)
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    wall_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}InteriorWallSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    text = "\n{id} = IFCWALL({guid}, $, 'bldg:WallSurface', ' ',$,$, {sh_id}, $,); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid)
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    wall_id_list.append(ifcsurfaceid)

                if(Boundary.find('{%s}CeilingSurface' %ns_bldg)):
                    ifcsurfaceid="#"+str(next(counter))
                    text = "\n{id} = IFCCOVERING ({guid}, $, 'CoveringSlab', ' ',$,$, {sh_id}, $,); "
                    text = text.format(id=ifcsurfaceid, guid=guid(), sh_id=ifcproductdefiniteshapeid)
                    FILE.write(text)
                    ifcsurfaceid_list.append(ifcsurfaceid)
                    roof_id_list.append(ifcsurfaceid)


        if (ifcsurfaceid_list):

            # print("#"+str(next(counter))," = IFCRELAGGREGATES (",guid(),", #102, $, $, ",ifcprojectid,", (", ifcbuildingid,"));")
            # print("#"+str(next(counter))," = IFCRELCONTAINEDINSPATIALSTRUCTURE (",guid(),", #102, $, $, (", end=' ')
            loop_string = ""
            for Element_id in ifcsurfaceid_list:
                loop_string += (str((Element_id)).strip("''"))
                loop_string += (",")
                loop_string2 = loop_string[:-1]
            # print(loop_string2, "),",ifcbuildingid,");")

            text = "\n#{id_1} = IFCRELAGGREGATES ( {guid_1},#102, $, $, {proj_id}, ({building_id}));"
            text += "\n#{id_2} = IFCRELCONTAINEDINSPATIALSTRUCTURE ({guid_2}, #102, $, $, ({lstring}), {building_id});"
            text = text.format(
                id_1 = next(counter),
                id_2 = next(counter),
                guid_1 = guid(),
                guid_2 = guid(),
                proj_id = ifcprojectid,
                lstring = loop_string2,
                building_id = ifcbuildingid
            )
            FILE.write(text)
    #Added material when needed by commenting the below back in

    #assign material #115 to all walls
    #print("#"+str(next(counter))," = IFCRELASSOCIATESMATERIAL (",guid(),",#102,$,$,(", end=' ')
    loop_string = ""
    for Element_id in wall_id_list:
        loop_string += (str((Element_id)).strip("''"))
        loop_string += (",")
        loop_string2 = loop_string[:-1]

    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#115);"
    text = text.format(id = next(counter),guid = guid(),lstring = loop_string2)
    FILE.write(text)

    #assign material #116 to all roofs
    loop_string = ""
    for Element_id in roof_id_list:
        loop_string += (str((Element_id)).strip("''"))
        loop_string += (",")
        loop_string2 = loop_string[:-1]
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#116);"
    text = text.format(id=next(counter), guid=guid(), lstring=loop_string2)
    FILE.write(text)

    #assign material #117 to all floors
    loop_string = ""
    for Element_id in floor_id_list:
        loop_string += (str((Element_id)).strip("''"))
        loop_string += (",")
        loop_string2 = loop_string[:-1]
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#117);"
    text = text.format(id=next(counter), guid=guid(), lstring=loop_string2)
    FILE.write(text)
    #assign material #118 to all ground
    loop_string = ""
    for Element_id in ground_id_list:
        loop_string += (str((Element_id)).strip("''"))
        loop_string += (",")
        loop_string2 = loop_string[:-1]
    text = "\n#{id} = IFCRELASSOCIATESMATERIAL ({guid},#102,$,$,({lstring}),#118);"
    text = text.format(id=next(counter), guid=guid(), lstring=loop_string2)
    FILE.write(text)

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
                text = "{id} = IFCCARTESIANPOINT (({points}));"
                text = text.format(id = ifc_id,points = str(bounding_points [pl]).strip("[]"))
                FILE.write(text)
                ifc_id_list.append(ifc_id)
                pl=pl+1
            ifcpolyloopid="#"+str(next(counter))

            #note; end= is used to identify what tp print after printstatment have ended
            loop_string = ""
            for Element_id in ifc_id_list:
                loop_string += (str((Element_id)).strip("''"))
                loop_string += (",")
                loop_string2 = loop_string[:-1]

            text ="\n{id} = IFCPOLYLOOP (({lstring}));"
            text = text.format(id = ifcpolyloopid,lstring = loop_string2)
            FILE.write(text)
            ifcfaceouterboundid="#"+str(next(counter))

            text = "\n{id} = IFCFACEOUTERBOUND ({pl_id}, .T.);"
            text = text.format(id = ifcfaceouterboundid,pl_id = ifcpolyloopid)
            FILE.write(text)

            ifcfaceid="#"+str(next(counter))
            text = "\n{id} = IFCFACE (({fo_id}));"
            text = text.format(id=ifcfaceid, pl_id=ifcfaceouterboundid)
            FILE.write(text)

            ifcopenshellid="#"+str(next(counter))
            text = "\n{id} = IFCOPENSHELL (({f_id}));"
            text = text.format(id=ifcopenshellid, pl_id=ifcfaceid)
            FILE.write(text)

            ifcshellbasedsurfacemodelid="#"+str(next(counter))
            text = "\n{id} = IFCSHELLBASEDSURFACEMODEL (({os_id}));"
            text = text.format(id=ifcshellbasedsurfacemodelid, os_id=ifcopenshellid)
            FILE.write(text)

            ifcshaperepresentationid="#"+str(next(counter))
            text = "\n{id} = IFCSHAPEREPRESENTATION ($,'Body','SurfaceModel',({id_2}));"
            text = text.format(id=ifcshaperepresentationid, id_2=ifcshellbasedsurfacemodelid)
            FILE.write(text)

            ifcproductdefiniteshapeid="#"+str(next(counter))
            text = "\n{id} = IFCPRODUCTDEFINITIONSHAPE ($, $, ({id_2}));"
            text = text.format(id=ifcproductdefiniteshapeid, id_2=ifcshaperepresentationid)
            FILE.write(text)

            text = "\n#{id} = IFCBUILDINGELEMENTPROXY( guid},#102,'Test extrude',$,$,#119,{id_2},$,$);"
            text = text.format(id =next(counter),guid = guid(),id_2 = ifcproductdefiniteshapeid)
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
    dst = "Result.ifc"
    CityGML2IFC(path, dst)

def to_csv_exportable_data(sf, origin):
    """
    모든 polyline 계열 데이터를 하나의 csv로 파일로 작성할 수 있게 변경한다
    """

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    data_to_export = list() 

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        for k in range(len(shp_rec.points)):
            e = shp_rec.points[k][0] - origin[0]
            n = shp_rec.points[k][1] - origin[1]
            z = shp_rec.z[k] - origin[2]

            data_to_export.append([e,n,z])

    return data_to_export
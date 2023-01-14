
import os, sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))


def get_tranform_UTM52N_to_TMMid():
    """UTM52N을 TM중부로 변환하는 osr.CoordinateTransformation 클래스 인스턴스를 반환한다
    
    reference: https://gdal.org/tutorials/osr_api_tut.html#coordinate-transformation
    """
    from osgeo import osr
    source_prj = os.path.normpath(os.path.join(current_path, 'test_files/NGII_SHP2_UTM52N.prj'))
    target_prj = os.path.normpath(os.path.join(current_path, 'test_files/NGII_SHP1_TM중부.prj'))
 
    return get_srs_transform(source_prj, target_prj)


def get_tranform_UTMK_to_TMMid():
    """UTMK를 TM중부로 변환하는 osr.CoordinateTransformation 클래스 인스턴스를 반환한다
    
    reference: https://gdal.org/tutorials/osr_api_tut.html#coordinate-transformation
    """
    from osgeo import osr
    source_prj = os.path.normpath(os.path.join(current_path, 'test_files/NGII_SHP2_UTMK.prj'))
    target_prj = os.path.normpath(os.path.join(current_path, 'test_files/NGII_SHP1_TM중부.prj'))
 
    return get_srs_transform(source_prj, target_prj)


def get_srs_transform(source_prj, target_prj):
    """
    reference: https://gdal.org/tutorials/osr_api_tut.html#coordinate-transformation
    """
    from osgeo import osr
    source_srs = osr.SpatialReference()
    target_srs = osr.SpatialReference()

    with open(source_prj, 'r') as prj_file:
        print('[INFO] Successfully read source_prj')
        prj_txt = prj_file.read()
        source_srs.ImportFromESRI([prj_txt])

    with open(target_prj, 'r') as prj_file:
        print('[INFO] Successfully read target_prj')
        prj_txt = prj_file.read()
        target_srs.ImportFromESRI([prj_txt])

    transform = osr.CoordinateTransformation(source_srs, target_srs)
    return transform



        
if __name__ == '__main__':
    tranform = get_tranform_TMMid_to_UTM52N()
    print('END')

    
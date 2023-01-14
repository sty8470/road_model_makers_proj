# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

import os

current_path = os.path.abspath(os.path.join('.'))
src_path = os.path.abspath(os.path.join(current_path, '..'))
mgeo_editor_path = os.path.abspath(os.path.join(src_path, 'proj_mgeo_editor_morai_opengl'))
lib_path = os.path.abspath(os.path.join(current_path, '..', 'lib'))

print('current_path : {}'.format(current_path))
print('src_path : {}'.format(src_path))
print('mgeo_editor_path : {}'.format(mgeo_editor_path))
print('lib_path : {}'.format(lib_path))

a = Analysis(['sign_in_window.py'],
             pathex=[current_path,
                src_path,
                os.path.abspath(os.path.join(src_path, 'uic')),
                mgeo_editor_path,
               os.path.abspath(os.path.join(mgeo_editor_path, 'GUI')),
               lib_path,               
               os.path.abspath(os.path.join(lib_path, 'common')),
               os.path.abspath(os.path.join(lib_path, 'mgeo')),
               os.path.abspath(os.path.join(lib_path, 'mgeo', 'edit', 'funcs')),
               os.path.abspath(os.path.join(lib_path, 'mscenario', 'class_defs')),
               os.path.abspath(os.path.join(lib_path, 'widget')),
			   os.path.abspath(os.path.join(lib_path, 'openscenario')),
			   os.path.abspath(os.path.join(lib_path, 'openscenario', 'client'))
             ],
             binaries=[],
             datas=[(os.path.join(mgeo_editor_path, 'GUI', '*.json'), './proj_mgeo_editor_morai_opengl/GUI'),
				(os.path.join(mgeo_editor_path, 'map.ico'), '.')
			 ],
             hiddenimports=['vtkmodules', 'vtkmodules.all', 'osgeo.gdal'],
             hookspath=[mgeo_editor_path],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [('v', None, 'OPTION')],
          exclude_binaries=True,
          name='MapViewer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
		  icon=os.path.join(mgeo_editor_path, 'map.ico') )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='sign_in_window')

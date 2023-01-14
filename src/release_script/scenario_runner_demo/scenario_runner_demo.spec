# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

current_path = os.path.abspath(os.path.join('.'))
root_path = os.path.abspath(os.path.join(current_path, '..'))
lib_path = os.path.abspath(os.path.join(current_path, '..', 'lib'))

a = Analysis(['scenario_runner_demo.py'],
             pathex=[current_path,
				root_path,
				lib_path,
				os.path.abspath(os.path.join(lib_path, 'mgeo')),
				os.path.abspath(os.path.join(root_path, 'proj_mgeo_editor_license_management')),
			    os.path.abspath(os.path.join(lib_path, 'openscenario')),
			    os.path.abspath(os.path.join(lib_path, 'openscenario', 'client'))],
             binaries=[],
             datas=[],
             hiddenimports=['vtkmodules', 'vtkmodules.all'],
             hookspath=[],
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
          [],
          exclude_binaries=True,
          name='scenario_runner_demo',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='scenario_runner_demo')

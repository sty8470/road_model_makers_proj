@echo off
@rem PyInstaller 를 이용한 패키징
pyinstaller --noconfirm main_opengl_editor.spec

@rem User 설정파일을 암호화하여 복사. 매개변수가 없으면 기본으로 모라이 설정파일이 복사된다.
set USER_FILE=%~1
if not defined USER_FILE (
	set USER_FILE=".\GUI\Users\User_MORAI.json"
)
python ..\lib\common\aes_cipher.py -m enc -i %USER_FILE% -o dist\main_opengl_editor\User.json
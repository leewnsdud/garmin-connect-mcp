#!/usr/bin/env python3
"""
Claude Desktop MCP 설정 자동화 스크립트
사용자별 맞춤 설정으로 Claude Desktop에 Garmin Connect MCP 서버를 추가합니다.
"""
import os
import json
import platform
from pathlib import Path
from dotenv import load_dotenv

def get_claude_desktop_config_path():
    """운영체제별 Claude Desktop 설정 파일 경로를 반환합니다."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    else:
        raise OSError(f"지원하지 않는 운영체제: {system}")

def get_project_path():
    """현재 프로젝트의 절대 경로를 반환합니다."""
    return Path(__file__).parent.absolute()

def get_uv_path():
    """uv 실행 파일의 경로를 찾습니다."""
    import shutil
    uv_path = shutil.which("uv")
    if not uv_path:
        raise FileNotFoundError("uv가 설치되어 있지 않습니다. https://docs.astral.sh/uv/ 에서 설치하세요.")
    return uv_path

def get_credentials():
    """사용자 자격증명을 가져옵니다."""
    # 먼저 .env 파일에서 확인
    load_dotenv()
    username = os.getenv("GARMIN_USERNAME")
    password = os.getenv("GARMIN_PASSWORD")
    
    if username and password:
        print(f"📋 기존 자격증명 발견: {username}")
        use_existing = input("기존 자격증명을 사용하시겠습니까? (y/n): ").lower().strip()
        if use_existing in ['y', 'yes', '']:
            return username, password
    
    print("\n📝 Garmin Connect 자격증명을 입력하세요:")
    
    while True:
        username = input("이메일 주소: ").strip()
        if username and '@' in username:
            break
        print("❌ 유효한 이메일 주소를 입력하세요")
    
    import getpass
    while True:
        password = getpass.getpass("비밀번호: ")
        if password:
            break
        print("❌ 비밀번호를 입력하세요")
    
    return username, password

def update_claude_desktop_config():
    """Claude Desktop 설정 파일을 업데이트합니다."""
    
    print("🏃‍♂️ Claude Desktop MCP 설정 - Garmin Connect")
    print("=" * 60)
    
    try:
        # 설정 파일 경로 확인
        config_path = get_claude_desktop_config_path()
        print(f"📁 설정 파일 경로: {config_path}")
        
        # 프로젝트 경로 확인
        project_path = get_project_path()
        print(f"📁 프로젝트 경로: {project_path}")
        
        # uv 경로 확인
        uv_path = get_uv_path()
        print(f"🔧 uv 경로: {uv_path}")
        
        # 자격증명 가져오기
        username, password = get_credentials()
        
        # 기존 설정 파일 읽기 또는 새로 생성
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("📖 기존 설정 파일을 불러왔습니다.")
        else:
            config = {"mcpServers": {}}
            config_path.parent.mkdir(parents=True, exist_ok=True)
            print("📄 새 설정 파일을 생성합니다.")
        
        # mcpServers 섹션이 없으면 생성
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Garmin Connect MCP 서버 설정 추가
        server_config = {
            "command": str(uv_path),
            "args": [
                "run",
                "--directory",
                str(project_path),
                "python",
                "main.py"
            ],
            "env": {
                "GARMIN_USERNAME": username,
                "GARMIN_PASSWORD": password
            }
        }
        
        # 기존 garmin-connect 설정이 있으면 확인
        if "garmin-connect" in config["mcpServers"]:
            print("⚠️  기존 garmin-connect 설정이 발견되었습니다.")
            overwrite = input("덮어쓰시겠습니까? (y/n): ").lower().strip()
            if overwrite not in ['y', 'yes', '']:
                print("❌ 설정이 취소되었습니다.")
                return False
        
        config["mcpServers"]["garmin-connect"] = server_config
        
        # 설정 파일 저장
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Claude Desktop 설정이 완료되었습니다!")
        print("\n📋 추가된 설정:")
        print(f"   서버 이름: garmin-connect")
        print(f"   명령어: {uv_path}")
        print(f"   프로젝트 경로: {project_path}")
        print(f"   사용자명: {username}")
        
        print("\n🔄 다음 단계:")
        print("1. Claude Desktop을 완전히 종료하세요 (Cmd+Q 또는 Alt+F4)")
        print("2. Claude Desktop을 다시 시작하세요")
        print("3. 다음과 같이 테스트해보세요:")
        print('   "내 최근 달리기 기록을 분석해줘"')
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 중 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        return False

def remove_claude_desktop_config():
    """Claude Desktop에서 Garmin Connect MCP 설정을 제거합니다."""
    
    try:
        config_path = get_claude_desktop_config_path()
        
        if not config_path.exists():
            print("❌ Claude Desktop 설정 파일이 존재하지 않습니다.")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "mcpServers" not in config or "garmin-connect" not in config["mcpServers"]:
            print("❌ garmin-connect MCP 서버 설정이 존재하지 않습니다.")
            return False
        
        # garmin-connect 설정 제거
        del config["mcpServers"]["garmin-connect"]
        
        # 설정 파일 저장
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ garmin-connect MCP 서버 설정이 제거되었습니다.")
        print("🔄 Claude Desktop을 재시작하세요.")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 제거 중 오류가 발생했습니다: {e}")
        return False

def show_current_config():
    """현재 Claude Desktop 설정을 표시합니다."""
    
    try:
        config_path = get_claude_desktop_config_path()
        
        if not config_path.exists():
            print("❌ Claude Desktop 설정 파일이 존재하지 않습니다.")
            return
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print("📝 MCP 서버 설정이 없습니다.")
            return
        
        print("📋 현재 MCP 서버 설정:")
        for server_name, server_config in config["mcpServers"].items():
            print(f"  • {server_name}")
            if server_name == "garmin-connect":
                print(f"    ✅ Garmin Connect MCP 서버가 설정되어 있습니다.")
        
    except Exception as e:
        print(f"❌ 설정 확인 중 오류가 발생했습니다: {e}")

def main():
    """메인 함수"""
    
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "add":
            update_claude_desktop_config()
        elif command == "remove":
            remove_claude_desktop_config()
        elif command == "show":
            show_current_config()
        elif command in ["help", "-h", "--help"]:
            print("🏃‍♂️ Claude Desktop MCP 설정 스크립트")
            print("=" * 50)
            print("사용법:")
            print("  python setup_claude_desktop.py add     # MCP 서버 추가")
            print("  python setup_claude_desktop.py remove  # MCP 서버 제거")
            print("  python setup_claude_desktop.py show    # 현재 설정 확인")
            print("  python setup_claude_desktop.py help    # 도움말 표시")
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print("'python setup_claude_desktop.py help' 를 실행하여 사용법을 확인하세요.")
    else:
        update_claude_desktop_config()

if __name__ == "__main__":
    main()
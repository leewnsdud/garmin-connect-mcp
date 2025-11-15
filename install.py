#!/usr/bin/env python3
"""
Garmin Connect MCP 서버 통합 설치 스크립트
모든 설정을 한 번에 처리합니다.
"""
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """필수 요구사항을 확인합니다."""
    print("🔍 시스템 요구사항 확인 중...")
    
    # Python 버전 확인
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 이상이 필요합니다.")
        print(f"   현재 버전: {sys.version}")
        return False
    else:
        print(f"✅ Python 버전: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # uv 설치 확인
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv 설치됨: {result.stdout.strip()}")
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("❌ uv가 설치되어 있지 않습니다.")
        print("   설치 방법: https://docs.astral.sh/uv/getting-started/installation/")
        return False
    
    return True

def install_dependencies():
    """프로젝트 의존성을 설치합니다."""
    print("\n📦 의존성 설치 중...")
    
    try:
        # uv sync 실행
        subprocess.run(["uv", "sync"], check=True, capture_output=True, text=True)
        print("✅ 의존성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        print(f"   출력: {e.stdout}")
        print(f"   오류: {e.stderr}")
        return False

def setup_environment():
    """환경 변수를 설정합니다."""
    print("\n🔧 환경 설정 중...")
    
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if env_file.exists():
        print("📋 .env 파일이 이미 존재합니다.")
        return True
    
    if env_template.exists():
        import shutil
        shutil.copy(env_template, env_file)
        print("📋 .env.template에서 .env 파일을 생성했습니다.")
        print("⚠️  .env 파일을 편집하여 Garmin Connect 자격증명을 입력하세요.")
    else:
        print("❌ .env.template 파일을 찾을 수 없습니다.")
        return False
    
    return True

def run_authentication_setup():
    """인증 설정을 실행합니다."""
    print("\n🔐 Garmin Connect 인증 설정...")
    
    try:
        # 대화형 인증 설정 실행
        subprocess.run(["uv", "run", "python", "setup_garmin_auth.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 인증 설정 실패: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ 사용자가 인증 설정을 취소했습니다.")
        return False

def setup_claude_code():
    """Claude Code MCP 설정을 추가합니다."""
    print("\n📱 Claude Code MCP 설정 중...")
    
    try:
        # Claude Code에 MCP 서버 추가
        subprocess.run([
            "claude", "mcp", "add", "garmin-connect", 
            "uv", "run", "python", "main.py"
        ], check=True, capture_output=True, text=True, cwd=Path.cwd())
        
        print("✅ Claude Code MCP 서버가 추가되었습니다.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Claude Code MCP 설정 실패: {e}")
        print("   수동으로 다음 명령어를 실행하세요:")
        print("   claude mcp add garmin-connect uv run python main.py")
        return False
    except FileNotFoundError:
        print("⚠️  Claude Code CLI가 설치되어 있지 않습니다.")
        print("   Claude Code를 먼저 설치하세요: https://claude.ai/code")
        return False

def setup_claude_desktop():
    """Claude Desktop MCP 설정을 추가합니다."""
    print("\n🖥️  Claude Desktop MCP 설정 중...")
    
    try:
        # Claude Desktop 설정 스크립트 실행
        subprocess.run(["uv", "run", "python", "setup_claude_desktop.py", "add"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Claude Desktop 설정 실패: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ 사용자가 Claude Desktop 설정을 취소했습니다.")
        return False

def run_final_test():
    """최종 테스트를 실행합니다."""
    print("\n🧪 설치 확인 테스트 중...")
    
    try:
        # 인증 상태 확인
        subprocess.run([
            "uv", "run", "python", "setup_garmin_auth.py", "check"
        ], check=True, capture_output=True, text=True)
        
        print("✅ 설치 및 설정이 완료되었습니다!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  일부 설정에 문제가 있을 수 있습니다: {e}")
        return False

def main():
    """메인 설치 함수"""
    
    print("🏃‍♂️ Garmin Connect MCP 서버 설치")
    print("=" * 60)
    print("이 스크립트는 Garmin Connect MCP 서버를 완전히 설정합니다.")
    print()
    
    # 단계별 설치 진행
    steps = [
        ("시스템 요구사항 확인", check_requirements),
        ("의존성 설치", install_dependencies),
        ("환경 설정", setup_environment),
        ("Garmin Connect 인증", run_authentication_setup),
        ("Claude Code 설정", setup_claude_code),
        ("Claude Desktop 설정", setup_claude_desktop),
        ("설치 확인", run_final_test),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 단계: {step_name}")
        print("-" * 40)
        
        if not step_func():
            print(f"\n❌ '{step_name}' 단계에서 오류가 발생했습니다.")
            print("설치를 중단합니다.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 설치가 완료되었습니다!")
    print()
    print("📋 다음 단계:")
    print("1. Claude Desktop을 재시작하세요")
    print("2. Claude Code를 재시작하세요")
    print("3. 다음과 같이 테스트해보세요:")
    print('   "내 최근 달리기 기록을 분석해줘"')
    print('   "10km 45분 기록으로 훈련 페이스를 계산해줘"')
    print()
    print("🛠️  문제가 있는 경우:")
    print("   uv run python setup_garmin_auth.py check")
    print("   uv run python setup_claude_desktop.py show")

if __name__ == "__main__":
    main()
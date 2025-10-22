# 손주톡톡 (Sonju TokTok)
> 시니어를 위한 AI 어시스턴트 앱 👵🤖  

---

## 📁 프로젝트 구조


---

## 👥 팀 구성
| 이름 | 역할 |
|------|------|
| 김준환 | PM / Infra |
| 안정규 | BE / File|
| 안근형 | BE / AI |
| 문희경 | FE / Design |
| 박지선 | FE / Design |
| 오동석 | AI / File |
---

## ⚙️ 브랜치 규칙
| 구분 | 브랜치명 | 설명 |
|------|-----------|------|
| 공용 개발 | `develop` | FE, BE 통합 테스트용 |
| 프론트 작업 | `feature/fe-*` | React Native UI |
| 백엔드 작업 | `feature/be-*` | API 라우팅 / DB 연결 |
| 배포 버전 | `main` | 안정화 완료본 |

---

## 🚀 개발 시작 가이드
```bash
# 저장소 클론
git clone https://github.com/joon041290/sonjutoktok.git

# develop 브랜치로 이동
git checkout develop

# 각자 작업 브랜치 생성
git checkout -b feature/fe-auth   # 프론트 예시

# dnd-html Skill

Skill format bài viết thành HTML chuẩn SEO cho **Mắt Quốc Tế Đà Nẵng** (matquoctednd.vn).

## Cấu trúc thư mục

```
html-dnd-script/
├── SKILL.md                    # Skill chính — copy vào Antigravity skills/dnd-html/
├── scripts/
│   └── push_to_github.py       # Script push HTML lên repo dnd-html-content
├── git_push_helper.py          # Helper dùng chung — copy vào workspace root
├── tools/
│   └── github_token_manager.py # Token manager — copy vào workspace tools/
└── credentials/
    └── token_config.json       # Cấu hình token — cần điền token thật
```

## Setup trên máy mới

### 1. Copy SKILL.md vào Antigravity

```
%APPDATA%\.gemini\config\skills\dnd-html\SKILL.md
%APPDATA%\.gemini\config\skills\dnd-html\scripts\push_to_github.py
```

### 2. Chuẩn bị workspace `tool-integration-phase02`

Tạo thư mục tại `C:\Users\Admin\tool-integration-phase02\` với cấu trúc:

```
tool-integration-phase02/
├── git_push_helper.py          ← copy từ repo này
├── tools/
│   └── github_token_manager.py ← copy từ repo này
└── credentials/
    ├── token_config.json       ← copy và điền GitHub token thật
    └── github_token.txt        ← chứa GitHub PAT token
```

### 3. Điền GitHub Token

Tạo file `credentials/github_token.txt` chứa GitHub Personal Access Token (PAT) có quyền `repo`.

Cấu hình `credentials/token_config.json`:
```json
{
  "tokens": [
    {
      "alias": "main",
      "file_path": "credentials/github_token.txt",
      "scopes": ["repo"],
      "repos": ["minhtranquang1993/dnd-html-content"]
    }
  ]
}
```

### 4. Kiểm tra hoạt động

Thử gọi:
```
/dnd-html keyword="lasik tphcm" images=3 link="Nội dung bài viết test..."
```

## Sử dụng

```
/dnd-html keyword="..." images=N link=(google docs URL | text)
```

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `keyword` | ✅ | Từ khóa chính |
| `images` | ❌ | Số LSI image keywords (mặc định 3) |
| `link` | ✅ | Google Docs URL hoặc text trực tiếp |
| `none-internal` | ❌ | Bỏ qua internal links và block bác sĩ |

## Lưu ý

- **GitHub token hết hạn**: Cập nhật file `credentials/github_token.txt`
- **Repo đầu ra**: `minhtranquang1993/dnd-html-content`
- **Không tạo `<h1>`** — CMS đã có title riêng

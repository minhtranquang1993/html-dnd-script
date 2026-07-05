---
name: dnd-html
description: >
  Format bài viết thành HTML chuẩn SEO cho website matquoctednd.vn.
  Trigger khi user gọi /dnd-html [post|event|doctor] kèm nội dung paste
  trực tiếp hoặc Google Docs URL (không cần khai báo keyword/link). Tự
  suy ra từ khóa SEO chính từ nội dung, format HTML có internal links
  hardcoded, sinh schema.org JSON-LD phù hợp theo loại bài
  (post/event/doctor), tạo LSI image keywords cho SEO on-page.
  Dùng cho: chuẩn bị bài đăng CMS, SEO content DND, format HTML bài viết mắt,
  bài event/hội thảo, trang thông tin bác sĩ.
homepage: skills/dnd-html
metadata:
  version: "2.0.0"
  author: openclaw
  category: seo
  risk: low
  scripts: true
  status: active
  triggers:
    - "/dnd-html"
    - "/dnd-html post"
    - "/dnd-html event"
    - "/dnd-html doctor"
    - "format html dnd"
    - "chuẩn bị bài html dnd"
    - "format bài viết matquoctednd"
---

# Skill: dnd-html

Format bài viết thành HTML chuẩn SEO cho website **Mắt Quốc Tế Đà Nẵng** (matquoctednd.vn). Router chọn 1 trong 3 loại bài, mỗi loại có workflow + schema.org riêng.

## Usage

```
/dnd-html [post|event|doctor] [images=N] [none-internal]
{nội dung paste trực tiếp, hoặc Google Docs URL}
```

Không cần khai báo `keyword=` hay `link="..."` — dán nội dung (hoặc dán URL Google Docs) ngay sau các flag, skill tự đọc và tự xác định từ khóa chính từ nội dung đó.

### Tham số

| Tham số | Bắt buộc | Áp dụng | Mô tả |
|---|---|---|---|
| `{type}` | ❌ | tất cả | `post` / `event` / `doctor`. Không truyền hoặc không khớp → mặc định `post` |
| `images` | ❌ | tất cả | Số lượng LSI image keywords (mặc định = 3) |
| `none-internal` | ❌ | post | Bỏ qua internal links (BƯỚC 3) và block bác sĩ tham vấn (BƯỚC 3.5). Không áp dụng cho event/doctor (2 loại này không có block bác sĩ tham vấn) |
| nội dung | ✅ | tất cả | Toàn bộ phần còn lại của message: text paste trực tiếp, hoặc 1 Google Docs URL |

### Ví dụ gọi

```
/dnd-html post images=5
Lasik là phương pháp phẫu thuật khúc xạ... (toàn bộ nội dung bài paste ở đây)
```

```
/dnd-html event
https://docs.google.com/document/d/1abc.../edit
```

```
/dnd-html doctor
BS Bùi Quang Tuấn là bác sĩ nội trú... (nội dung giới thiệu bác sĩ)
```

> Tương thích ngược: nếu user vẫn gõ theo cú pháp cũ `keyword="..." link="..."`, hiểu `link` là nội dung/URL, `keyword` chỉ dùng như gợi ý ưu tiên thêm (không bắt buộc phải khớp) — vẫn xử lý được, nhưng không cần yêu cầu user gõ theo cú pháp đó nữa.

---

## BƯỚC 0 — Type Detection

Đọc token ngay sau `/dnd-html`:

- Token là `post` (không phân biệt hoa/thường) → **loại POST**
- Token là `event` → **loại EVENT**
- Token là `doctor` → **loại DOCTOR**
- Token là tên tham số (`keyword=`, `link=`, ...) hoặc không có token nào, hoặc token không khớp 3 giá trị trên → **mặc định loại POST**, coi token đó (nếu có) như phần đầu của tham số kế tiếp

Nếu type không rõ ràng (ví dụ user gõ nhầm `doctors`, `su-kien`) → hỏi lại user xác nhận loại, KHÔNG tự đoán.

Sau khi xác định loại, đọc file reference tương ứng và làm theo workflow đầy đủ trong đó:

| Loại | File workflow |
|---|---|
| post | `references/post.md` |
| event | `references/event.md` |
| doctor | `references/doctor.md` |

---

## BƯỚC 1 — Đọc Content (chung cho cả 3 loại)

**Nếu nội dung sau flag là 1 Google Docs URL (và không có gì khác):**
1. Extract document ID từ URL (phần giữa `/d/` và `/edit` hoặc `/view`)
2. Gọi tool `mcp__google-workspace__docs_get_document` với:
   - `document_id`: ID vừa extract
   - `response_format`: `"markdown"`
3. Dùng content trả về làm nguồn

**Nếu là text thuần (đã paste trực tiếp):**
- Dùng trực tiếp làm nguồn content

**Xác định keyword chính:** đọc nội dung, tự rút ra từ khóa SEO chính (chủ đề trọng tâm của bài — thường là cụm từ xuất hiện ở tiêu đề/đoạn mở đầu hoặc lặp lại nhiều nhất mang tính chủ đề). Dùng keyword này cho toàn bộ các bước sau (internal links, SEO title/slug...). Nếu user có kèm gợi ý keyword rõ ràng trong message → ưu tiên gợi ý đó hơn là tự suy luận.

Sau bước này, chuyển sang workflow riêng của từng loại (`references/{type}.md`) để format HTML + sinh schema.

---

## BƯỚC 5 — Push HTML lên GitHub (chung cho cả 3 loại)

Sau khi có HTML hoàn chỉnh (đã bao gồm JSON-LD script tag từ workflow riêng), push lên repo `minhtranquang1993/dnd-html-content`.

**Tạo slug từ keyword:**
- Lowercase, bỏ dấu tiếng Việt, thay khoảng trắng và ký tự đặc biệt bằng `-`
- Ví dụ: `"phẫu thuật mắt lasik"` → `"phau-thuat-mat-lasik"`

**Lưu HTML vào file tạm rồi chạy script:**

```bash
python3 -c "
html = '''<article>...HTML content + JSON-LD script tag...</article>'''
open('/tmp/dnd_{slug}.html', 'w', encoding='utf-8').write(html)
"

python3 skills/dnd-html/scripts/push_to_github.py \
  --slug "{keyword-slug}" \
  --html-file /tmp/dnd_{slug}.html
```

Script trả về URL dạng:
```
https://github.com/minhtranquang1993/dnd-html-content/blob/main/{slug}.html
```

**Lưu URL này** để hoàn thiện thông tin trả về.

> ⚠️ Nếu script báo lỗi `Bad credentials` hoặc `No valid GitHub token`: token đã hết hạn. Báo user cập nhật token tại `credentials/github_token.txt`.

---

## Output Format (chung, mỗi loại thêm bảng riêng — xem cuối `references/{type}.md`)

```markdown
✅ **Bài viết DND đã sẵn sàng** ({type})

📌 **Keyword:** {keyword}
📝 **Title:** {seo_title}
💡 **Description:** {seo_description}
🌐 **Slug:** {slug}
🔗 **GitHub:** https://github.com/minhtranquang1993/dnd-html-content/blob/main/{slug}.html

---

## 🏷️ Schema.org đã sinh

| Schema | Áp dụng? | Lý do |
|---|---|---|
| {SchemaType1} | ✅/❌ | ... |

---

## 🖼️ LSI Image Keywords (N ảnh)

| # | Keyword tìm ảnh | Gợi ý Alt Text | Alt Text Slug |
|---|---|---|---|
| 1 | {lsi_keyword_1} | {alt_text_1} | {alt_slug_1} |

---

## 🔗 Internal Links đã chèn

| URL | Anchor Text |
|---|---|
| https://... | ... |

---

## 📄 HTML Content

<details>
<summary>Click để xem HTML content</summary>

\```html
<article>
  [NỘI DUNG HTML ĐÃ FORMAT + INTERNAL LINKS + JSON-LD]
</article>
\```
</details>
```

---

## Notes chung

- **Không tự thêm nội dung**: Tuyệt đối không viết thêm thông tin không có trong bản gốc
- **SEO-safe**: Mỗi URL internal link chỉ 1 lần để tránh over-optimization
- **JSON-LD**: Luôn serialize qua `json.dumps(obj, ensure_ascii=False)` khi viết ra file, không tự escape tay chuỗi JSON tiếng Việt
- **Mặc định images=3** nếu không truyền tham số
- **GitHub token**: nếu hết hạn, báo user cập nhật `credentials/github_token.txt`

---
name: dnd-html
description: >-
  Format bài viết thành HTML chuẩn SEO cho website matquoctednd.vn (Bệnh viện Mắt Quốc tế DND Sài Gòn).
  Trigger khi user gọi /dnd-html [post|event|doctor] kèm nội dung paste trực tiếp hoặc Google Docs URL
  (không cần khai báo keyword/link). Tự suy ra từ khóa SEO chính từ nội dung, format HTML có internal
  links hardcoded, sinh schema.org JSON-LD phù hợp theo loại bài (post/event/doctor), block bác sĩ
  tham vấn, tạo SEO title/description/slug + LSI image keywords, rồi hiển thị HTML output trực tiếp
  trên màn hình.
  Trigger: "/dnd-html", "format html dnd", "chuẩn bị bài html dnd", "format bài viết matquoctednd".
---

# Skill: dnd-html

Format bài viết thành HTML chuẩn SEO cho website **Bệnh viện Mắt Quốc tế DND Sài Gòn** (matquoctednd.vn). Router chọn 1 trong 3 loại bài, mỗi loại có workflow + schema.org riêng.

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
2. Gọi tool Google Workspace Docs (`mcpGoogleWorkspaceDocsGetDocument`) với:
   - `document_id`: ID vừa extract
   - `response_format`: `"markdown"`
3. Dùng content trả về làm nguồn

**Nếu là text thuần (đã paste trực tiếp):**
- Dùng trực tiếp làm nguồn content

**Xác định keyword chính:** đọc nội dung, tự rút ra từ khóa SEO chính (chủ đề trọng tâm của bài — thường là cụm từ xuất hiện ở tiêu đề/đoạn mở đầu hoặc lặp lại nhiều nhất mang tính chủ đề). Dùng keyword này cho toàn bộ các bước sau (internal links, SEO title/slug...). Nếu user có kèm gợi ý keyword rõ ràng trong message → ưu tiên gợi ý đó hơn là tự suy luận.

**Riêng type = event:** KHÔNG rút gọn thành từ khóa ngắn như trên. Từ khóa chính = tên đầy đủ của event/chương trình lấy từ content (thường ở dạng "WORKSHOP: {TÊN CHƯƠNG TRÌNH}" hoặc "HỘI THẢO: {TÊN CHƯƠNG TRÌNH}" — bỏ phần tagline/phụ đề phía sau dấu `|` nếu có, vì đó chỉ là mô tả thêm chứ không phải tên chương trình). Ví dụ content có `"WORKSHOP: SMILE PRO - XU HƯỚNG PHẪU THUẬT KHÚC XẠ HIỆN ĐẠI | NHỮNG ĐIỀU CẦN BIẾT TRƯỚC KHI MỔ CẬN"` → từ khóa chính = `"Workshop SMILE Pro - Xu hướng phẫu thuật khúc xạ hiện đại"`, dùng nguyên cụm này (không rút gọn thêm) để tạo slug ở bước dưới.

**Tạo Slug (ngay sau khi có keyword):** từ keyword chính vừa xác định, tạo slug dùng cho URL bài viết thật:
- Lowercase, bỏ dấu tiếng Việt, thay khoảng trắng và ký tự đặc biệt bằng `-`
- Ví dụ (post/doctor): `"phẫu thuật mắt lasik"` → `"phau-thuat-mat-lasik"`
- Ví dụ (event): `"Workshop SMILE Pro - Xu hướng phẫu thuật khúc xạ hiện đại"` → `"workshop-smile-pro-xu-huong-phau-thuat-khuc-xa-hien-dai"`

Slug này chỉ tính **một lần duy nhất** ở đây, dùng lại cho: block "Tóm tắt bài viết bằng AI" (cần URL bài viết thật `https://matquoctednd.vn/{slug}/` sớm hơn BƯỚC 5) và bảng Output Format ở BƯỚC 5. KHÔNG tính lại slug ở BƯỚC 5.

Sau bước này, chuyển sang workflow riêng của từng loại (`references/{type}.md`) để format HTML + sinh schema.

---

## BƯỚC 5 — Slug cho Output Format (chung cho cả 3 loại)

Slug đã được tính ở BƯỚC 1 (ngay sau khi xác định keyword). Dùng lại đúng slug đó để điền vào bảng Output Format — KHÔNG tính lại hoặc tạo slug mới ở đây.

---

## Output Format (chung, mỗi loại thêm bảng riêng — xem cuối `references/{type}.md`)

```markdown
✅ **Bài viết DND đã sẵn sàng** ({type})

📌 **Keyword:** {keyword}
📝 **Title:** {seo_title}
💡 **Description:** {seo_description}
🌐 **Slug:** {slug}

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

\```html
<article>
  [NỘI DUNG HTML ĐÃ FORMAT + INTERNAL LINKS + JSON-LD]
</article>
\```
```

---

## Notes chung

- **Không tự thêm nội dung**: Tuyệt đối không viết thêm thông tin không có trong bản gốc
- **SEO-safe**: Mỗi URL internal link chỉ 1 lần để tránh over-optimization
- **JSON-LD**: Luôn serialize/hiển thị đúng cú pháp JSON, không tự escape tay chuỗi JSON tiếng Việt
- **Mặc định images=3** nếu không truyền tham số

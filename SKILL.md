---
name: dnd-html
description: >
  Format bài viết thành HTML chuẩn SEO cho website matquoctednd.vn.
  Trigger khi user gọi /dnd-html với tham số keyword, images, link.
  Nhận content từ Google Docs URL hoặc text trực tiếp, format HTML có
  internal links hardcoded, tạo LSI image keywords cho SEO on-page.
  Dùng cho: chuẩn bị bài đăng CMS, SEO content DND, format HTML bài viết mắt.
homepage: skills/dnd-html
metadata:
  version: "1.1.0"
  author: openclaw
  category: seo
  risk: low
  scripts: true
  status: active
  triggers:
    - "/dnd-html"
    - "format html dnd"
    - "chuẩn bị bài html dnd"
    - "format bài viết matquoctednd"
---

# Skill: dnd-html

Format bài viết thành HTML chuẩn SEO cho website **Mắt Quốc Tế Đà Nẵng** (matquoctednd.vn). Nhận content qua Google Docs URL hoặc text, chèn internal links tự động, tạo LSI keywords cho ảnh.

## Usage

```
/dnd-html keyword="..." images=N link=(google docs URL | text content) [none-internal]
```

### Tham số

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `keyword` | ✅ | Từ khóa chính của bài viết (ví dụ: "lasik là gì", "phẫu thuật mắt tphcm") |
| `images` | ❌ | Số lượng LSI image keywords cần tạo (mặc định = 3) |
| `link` | ✅ | Google Docs URL hoặc nội dung text trực tiếp |
| `none-internal` | ❌ | Flag — nếu có thì BỎ QUA toàn bộ internal links (BƯỚC 3) và block bác sĩ tham vấn (BƯỚC 3.5) |

### Ví dụ gọi

```
/dnd-html keyword="lasik tphcm" images=5 link=https://docs.google.com/document/d/1abc.../edit
```

```
/dnd-html keyword="phẫu thuật mắt" link="Phẫu thuật mắt là phương pháp..."
```

```
/dnd-html keyword="cườm mắt" images=4 link=https://docs.google.com/... none-internal
```

---

## Workflow

### BƯỚC 1 — Đọc Content

**Nếu `link` là Google Docs URL:**
1. Extract document ID từ URL (phần giữa `/d/` và `/edit` hoặc `/view`)
2. Gọi tool `mcp__google-workspace__docs_get_document` với:
   - `document_id`: ID vừa extract
   - `response_format`: `"markdown"`
3. Dùng content trả về làm nguồn

**Nếu `link` là text thuần:**
- Dùng trực tiếp làm nguồn content

---

### BƯỚC 2 — Format HTML

**Rules bắt buộc — KHÔNG được vi phạm:**

- ❌ KHÔNG tạo `<h1>` (title đã có trên CMS, tạo `<h1>` sẽ duplicate)
- ✅ Wrap toàn bộ trong `<article>`
- ✅ Giữ nguyên 100% nội dung gốc — KHÔNG thêm/bớt thông tin
- ✅ KHÔNG tự ý viết thêm câu, đoạn, ý mới

**Cấu trúc heading theo nội dung:**

| Cấp độ | Tag | Dùng khi |
|---|---|---|
| Section lớn | `<h2>` | Chủ đề chính, phần lớn |
| Sub-section | `<h3>` | Mục con của h2 |
| Sub-sub-section | `<h4>` | Chỉ khi thực sự cần, không lạm dụng |

**Formatting elements:**

- Đoạn văn → `<p>`
- Danh sách không thứ tự → `<ul>` + `<li>`
- Danh sách có thứ tự / các bước → `<ol>` + `<li>`
- Từ/cụm từ quan trọng → `<strong>` (tối đa 1-2 lần/section, không lạm dụng)

---

### BƯỚC 3 — Chèn Internal Branding Links

> ⚠️ **Nếu có flag `none-internal`** → BỎ QUA toàn bộ BƯỚC 3 này, chuyển thẳng sang BƯỚC 4.

Tự động chèn **2-4 internal links** vào vị trí phù hợp nhất trong HTML.

**Danh sách URL hardcoded:**

```
Trang chủ:      https://matquoctednd.vn/
Smile Pro:      https://matquoctednd.vn/dich-vu/smile-pro/
Smart Sight:    https://matquoctednd.vn/dich-vu/smartsight/
Femto Pro:      https://matquoctednd.vn/dich-vu/femto-pro/
Femto Lasik:    https://matquoctednd.vn/dich-vu/femto-lasik/
Smart SurfACE:  https://matquoctednd.vn/dich-vu/smart-surface/
Phakic ICL:     https://matquoctednd.vn/dich-vu/phakic-icl/
BS Bùi Quang Tuấn:  https://matquoctednd.vn/doctors/bui-quang-tuan/
BS Lê Thị Thu Hà:   https://matquoctednd.vn/doctors/le-thi-thu-ha/
```

**Rules chèn link:**

1. **Anchor text TỰ NHIÊN** — chọn từ/cụm từ đã có sẵn trong nội dung, KHÔNG thêm câu mới chỉ để chèn link
2. **Mỗi URL tối đa 1 lần** trong toàn bài
3. **Ưu tiên dịch vụ liên quan** đến `keyword` chính:
   - keyword có "smile" → ưu tiên Smile Pro
   - keyword có "lasik" / "femto" → ưu tiên Femto Lasik, Femto Pro
   - keyword có "icl" / "phakic" → ưu tiên Phakic ICL
   - keyword có "cận thị nhẹ" / "không cần mổ" → ưu tiên Smart Sight
   - keyword liên quan đến tật khúc xạ nói chung → phân bổ đều
4. **Trang chủ** — chèn khi có cụm từ nhắc đến "Mắt Quốc Tế Đà Nẵng", tên phòng khám, hoặc "chúng tôi"
5. **Format link theo loại:**
   - **Internal link** (domain `matquoctednd.vn`): `<a href="URL">anchor text</a>`
   - **External link** (domain khác, ví dụ: Google Maps, Google Forms, YouTube...): `<a href="URL" rel="nofollow" target="_blank">anchor text</a>`
6. KHÔNG chèn link vào heading (`<h2>`, `<h3>`, `<h4>`)
7. **Áp dụng external rule cho toàn bộ bài** — kể cả các link có sẵn trong content gốc (maps.google, forms.gle, v.v.) cũng phải gắn `rel="nofollow" target="_blank"`

---

### BƯỚC 3.5 — Thêm Block Bác Sĩ Tham Vấn (BẮT BUỘC — trừ khi `none-internal`)

> ⚠️ **Nếu có flag `none-internal`** → BỎ QUA toàn bộ BƯỚC 3.5 này, chuyển thẳng sang BƯỚC 4.

**Luôn luôn chèn block này vào CUỐI bài**, ngay trước thẻ đóng `</article>`, sau đoạn kết bài.

**Nội dung cố định (KHÔNG thay đổi):**

```html
<p>Bài viết có sự tham vấn của 2 bác sĩ chuyên khoa mắt:</p>
<ol>
  <li><a href="https://matquoctednd.vn/doctors/bui-quang-tuan/">Bác sĩ nội trú Bùi Quang Tuấn – Giám Đốc Bệnh viện Mắt Quốc tế DND Sài Gòn</a></li>
  <li><a href="https://matquoctednd.vn/doctors/le-thi-thu-ha/">Thạc sĩ Bác sĩ Lê Thị Thu Hà – Trưởng khoa khúc xạ Bệnh viện Mắt Quốc tế DND Sài Gòn</a></li>
</ol>
```

**Rules:**
- ✅ LUÔN chèn block này vào cuối mỗi bài — trừ khi có flag `none-internal`
- ✅ Đặt SAU đoạn văn kết bài (thường là đoạn có hotline)
- ❌ KHÔNG thay đổi tên bác sĩ, chức danh, hay URL
- ❌ KHÔNG tính 2 link bác sĩ này vào giới hạn 2-4 internal links của BƯỚC 3

---

### BƯỚC 4 — Tạo SEO Meta Data & LSI Image Keywords

**1. Tạo SEO Title, Description & Slug:**
- **Title:** Viết 1 thẻ Title hấp dẫn, chứa `keyword` chính, độ dài 50-60 ký tự.
- **Description:** Viết 1 Meta Description tóm tắt nội dung thu hút, chứa `keyword` chính, độ dài 150-160 ký tự. Có Call-to-action.
- **Slug URL:** Trích xuất từ Title hoặc Keyword, viết thường, không dấu, ngăn cách bằng dấu `-`.

**2. Tạo LSI Image Keywords:**
Dựa vào `keyword` chính và nội dung bài, tạo **N keywords** (N = tham số `images`, mặc định 3) cho việc tìm ảnh stock.
- Mix giữa: keyword chính + modifier đa dạng (địa điểm, cảm xúc bệnh nhân, hành động bác sĩ, môi trường phẫu thuật, kết quả).
- Thêm **gợi ý alt text** ngắn (dưới 10 từ) cho từng ảnh.
- Thêm **alt text slug**: chuyển alt text sang dạng slug (lowercase, bỏ dấu tiếng Việt, thay khoảng trắng và ký tự đặc biệt bằng `-`). Dùng để đặt tên file ảnh chuẩn SEO.

---

### BƯỚC 5 — Push HTML lên GitHub

Sau khi có HTML hoàn chỉnh (BƯỚC 2 + 3), push lên repo `minhtranquang1993/dnd-html-content`.

**Tạo slug từ keyword:**
- Lowercase, bỏ dấu tiếng Việt, thay khoảng trắng và ký tự đặc biệt bằng `-`
- Ví dụ: `"phẫu thuật mắt lasik"` → `"phau-thuat-mat-lasik"`

**Lưu HTML vào file tạm rồi chạy script:**

```bash
# Ghi HTML ra file tạm
python3 -c "
import sys
html = '''<article>...HTML content...</article>'''
open('/tmp/dnd_{slug}.html', 'w', encoding='utf-8').write(html)
"

# Push lên GitHub
python3 skills/dnd-html/scripts/push_to_github.py \
  --slug "{keyword-slug}" \
  --html-file /tmp/dnd_{slug}.html
```

Script trả về URL dạng:
```
https://github.com/minhtranquang1993/dnd-html-content/blob/main/{slug}.html
```

**Lưu URL này** để hoàn thiện thông tin trả về.

> ⚠️ Nếu script báo lỗi `Bad credentials` hoặc `No valid GitHub token`: token đã hết hạn. Báo user cập nhật token tại `credentials/github_token.txt` hoặc `credentials/github_token_fire_gains.txt`.

---

## Output Format

Hiển thị kết quả ra màn hình chat theo đúng định dạng sau (nếu push GitHub thất bại, vẫn hiển thị format này và bỏ qua link GitHub):

```markdown
✅ **Bài viết DND đã sẵn sàng**

📌 **Keyword:** {keyword}
📝 **Title:** {seo_title}
💡 **Description:** {seo_description}
🌐 **Slug:** {slug}
🔗 **GitHub:** https://github.com/minhtranquang1993/dnd-html-content/blob/main/{slug}.html

---

## 🖼️ LSI Image Keywords (N ảnh)

| # | Keyword tìm ảnh | Gợi ý Alt Text | Alt Text Slug |
|---|---|---|---|
| 1 | {lsi_keyword_1} | {alt_text_1} | {alt_slug_1} |
| 2 | {lsi_keyword_2} | {alt_text_2} | {alt_slug_2} |
| N | ... | ... | ... |

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
  [NỘI DUNG HTML ĐÃ FORMAT + INTERNAL LINKS]
</article>
\```
</details>
```

---

## Examples

### Example 1 — Google Docs URL

**Input:**
```
/dnd-html keyword="phẫu thuật mắt lasik" images=4 link=https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
```

**Steps:**
1. Extract doc ID: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`
2. Call `mcp__google-workspace__docs_get_document` → nhận markdown content
3. Format HTML với `<article>`, `<h2>`, `<h3>`, `<p>`, `<ul>/<ol>`
4. Chèn 2-4 internal links (ưu tiên Femto Lasik, Femto Pro vì keyword có "lasik")
5. Tạo 4 LSI image keywords và tạo Title, Description, Slug chuẩn SEO
6. Push HTML lên GitHub → nhận URL `https://github.com/minhtranquang1993/dnd-html-content/blob/main/phau-thuat-mat-lasik.html`
7. In ra Output theo định dạng chuẩn

### Example 2 — Text trực tiếp

**Input:**
```
/dnd-html keyword="cườm mắt" images=3 link="Cườm mắt (đục thủy tinh thể) là tình trạng..."
```

**Steps:**
1. Nhận text trực tiếp làm source
2. Format HTML
3. Chèn internal links phù hợp (keyword "cườm mắt" → link tới trang chủ + dịch vụ liên quan)
4. Tạo 3 LSI image keywords và tạo Title, Description, Slug chuẩn SEO
5. Push HTML lên GitHub → nhận URL `https://github.com/minhtranquang1993/dnd-html-content/blob/main/cuom-mat.html`
6. In ra Output theo định dạng chuẩn

---

## Notes

- **Không tự thêm nội dung**: Tuyệt đối không viết thêm thông tin không có trong bản gốc
- **SEO-safe**: Chỉ 1 lần mỗi URL để tránh over-optimization
- **Anchor text tự nhiên**: Không làm lộ dấu hiệu link nhân tạo
- **Mặc định images=3** nếu không truyền tham số
- **GitHub token**: nếu hết hạn, báo user cập nhật `credentials/github_token.txt`

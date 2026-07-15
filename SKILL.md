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
| `images` | ❌ | tất cả | 2 chế độ: **số N** → sinh N LSI image keywords text (mặc định = 3, hành vi cũ). **đường dẫn folder** → bật xử lý ảnh thật (resize/convert/optimize) theo mục "Common Procedure — Xử lý & tối ưu ảnh folder" |
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

### Parse tham số `images=`

Xác định `images` là **count mode** (số N) hay **path mode** (folder ảnh thật) theo thứ tự ưu tiên (tránh nhầm folder tên toàn số như `2024`):

1. Value chứa ký tự phân tách path (`/` hoặc `\`) HOẶC là một directory tồn tại trên đĩa → **path mode** (chạy mục "Common Procedure — Xử lý & tối ưu ảnh folder").
2. Ngược lại, nếu value khớp `^\d+$` → **count mode** (N = giá trị đó).
3. Còn lại → count mode với default (`images=3`).

Khuyến nghị: khi truyền folder nên dùng đường dẫn có `/` (tuyệt đối hoặc `./relative`) để không mơ hồ. Tương thích ngược 100% với `images=N`.

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

## Common Procedure — Xử lý & tối ưu ảnh folder (khi images là path)

Mục này CHỈ chạy khi tham số `images` là **path** (xem "Parse tham số `images=`" ở BƯỚC 0). Nếu `images` là số → BỎ QUA toàn bộ mục này. Các reference (post/event/doctor) trỏ tới mục này bằng TÊN, không chỉ bằng số.

1. **Chỉ chạy khi path.** Số → bỏ qua, giữ hành vi LSI keyword cũ.
2. **Đọc folder, liệt kê ảnh nguồn** — sort theo alphabet ASCII bằng `sorted()`. Số ảnh = N. LSI keyword ở BƯỚC 4 sinh đúng N item, map 1-1 theo thứ tự alphabet.
3. **Hỏi user:** "Width bao nhiêu px? (mặc định 1200)". User không nêu → dùng 1200.
4. **Ghi manifest JSON tạm** `C:\tmp\dnd-optimize-manifest.json` (tạo `C:\tmp` nếu chưa có). Manifest là JSON array, mỗi item:

   ```json
   { "source_filename": "IMG_0012.PNG", "alt_text_slug": "rang-su-tham-my", "image_description": "Răng sứ thẩm mỹ tại phòng khám" }
   ```

   `source_filename` phải là tên file ĐÚNG như trên đĩa (không đoán lại theo slug).

   > **Metadata nhúng vào ảnh:** script tự ghi `image_description` vào cả EXIF Description lẫn field **Tags** (keyword, UTF-16 nên hiển thị đúng tiếng Việt trong Windows Properties), và field **Authors** = "Bệnh viện Mắt Quốc tế DND Sài Gòn" cho mọi ảnh. Metadata được ghi LẠI sau khi TinyPNG nén (TinyPNG strip metadata) nên luôn có mặt trong ảnh cuối — không cần khai báo gì thêm trong manifest.
5. **Gọi script** (quote mọi path):

   ```
   python "<SKILL_DIR>/scripts/optimize_images.py" --folder "<path folder>" --width <W> --manifest-file "C:\tmp\dnd-optimize-manifest.json"
   ```
6. **Parse JSON stdout.** Dùng `final_filename`/`final_path` THỰC TẾ trong output (không dùng slug dự đoán ban đầu) để điền bảng ảnh. `ok:false` → báo lỗi setup, không xử lý ảnh tiếp (vẫn tiếp tục phần HTML/schema bình thường).
7. **Báo tình trạng từng ảnh** (applied/fallback/failed) trong Output Format.

---

## Common Procedure — Nhúng video YouTube (post + event)

Áp dụng khi **BƯỚC 2 (Format HTML)** của `post` hoặc `event` gặp link YouTube. **KHÔNG áp dụng cho `doctor`**. post.md và event.md trỏ tới mục này bằng tên.

### Khi nào bung thành iframe (vs giữ external link)

- **URL YouTube đứng riêng** — chiếm trọn 1 dòng/đoạn trong content nguồn (dạng URL trần, hoặc bọc trong `[ ]` và có thể dư khoảng trắng, ví dụ: `[https://www.youtube.com/watch?v=Z2msLjuW2Wc ]`) → **bung thành iframe embed** (theo mục này). Xóa hẳn dòng URL gốc, thay bằng khối `<figure>` iframe — KHÔNG giữ lại text URL hay thẻ `<a>`.
- **Link YouTube nằm trong câu văn** (đóng vai trò anchor giữa một câu, ví dụ "xem video này để rõ hơn") → **KHÔNG bung iframe**, giữ external `<a href=".." rel="nofollow" target="_blank">` như rule external link thông thường (bung iframe giữa câu sẽ vỡ mạch đọc).

### Nhận diện URL & rút VIDEO_ID

Strip `[`, `]`, và khoảng trắng dư trước khi parse. Nhận diện 4 dạng, đều rút ra `VIDEO_ID`:

| Dạng URL | VIDEO_ID | Loại |
|---|---|---|
| `https://www.youtube.com/watch?v=VIDEO_ID` (bỏ param dư `&t=`, `&list=`... chỉ lấy `v`) | giá trị `v` | video thường |
| `https://youtu.be/VIDEO_ID` | phần sau `/` | video thường |
| `https://www.youtube.com/embed/VIDEO_ID` | phần sau `/embed/` | video thường |
| `https://www.youtube.com/shorts/VIDEO_ID` | phần sau `/shorts/` | **Shorts** |

**Playlist thuần** (chỉ có `list=`, KHÔNG có videoID đơn lẻ) → KHÔNG embed, giữ nguyên thành external `<a>`.

### Markup — 2 biến thể (style inline, theo tỉ lệ khung)

Toàn bộ style viết inline trực tiếp trên tag (CMS thường strip `<style>`). `src` luôn dùng `https://www.youtube.com/embed/VIDEO_ID`.

**Video thường** (16:9, ngang):

```html
<figure style="max-width: 680px; margin: 20px auto; text-align: center;">
<div style="position: relative; width: 100%; aspect-ratio: 16/9;"><iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" title="YouTube video player" src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0" allowfullscreen="allowfullscreen"></iframe></div>
<figcaption style="padding-top: 12px; font-size: 14px; line-height: 1.5; color: #555;">{caption}</figcaption>
</figure>
```

**Shorts** (9:16, dọc):

```html
<figure style="max-width: 315px; margin: 20px auto; text-align: center;">
<div style="position: relative; width: 100%; aspect-ratio: 9/16;"><iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" title="YouTube Shorts player" src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0" allowfullscreen="allowfullscreen"></iframe></div>
<figcaption style="padding-top: 12px; font-size: 14px; line-height: 1.5; color: #555;">{caption}</figcaption>
</figure>
```

### Caption (`<figcaption>`) — tự sinh từ ngữ cảnh

Sinh caption ngắn **6-12 từ**, bám sát chủ đề đoạn chứa video (dựa vào heading section + câu văn ngay trước dòng URL).

- ✅ Chỉ diễn đạt lại chủ đề đã có trong đoạn văn (ví dụ video nằm trong section "SmartSight" → `"Video minh họa phương pháp SmartSight"`)
- ❌ KHÔNG thêm chi tiết mới không có trong content (không nói "bác sĩ X thực hiện" nếu đoạn đó không nhắc)
- ❌ KHÔNG khẳng định nội dung video mà text xung quanh không đề cập

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
```

**Chỉ khi `images` là path** — thêm bảng sau (điền từ JSON output của `optimize_images.py`, dùng `final_filename` thực tế):

```markdown
## 🖼️ Ảnh đã xử lý

| # | File nguồn | File output | Trạng thái | TinyPNG |
|---|---|---|---|---|
| 1 | {source_filename} | {final_filename} | success/fallback/failed | applied/skipped_no_key/skipped_error/disabled_quota |

**Tổng kết:** total {n} · success {n} · fallback {n} · failed {n}

---
```

```markdown

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
- **Nhúng video YouTube** (post + event): URL YouTube đứng riêng 1 dòng → bung thành iframe embed, xem mục "Common Procedure — Nhúng video YouTube"

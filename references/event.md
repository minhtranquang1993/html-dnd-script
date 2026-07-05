# Workflow: EVENT (hội thảo, workshop)

Áp dụng khi type = `event`. Tiếp nối sau BƯỚC 1 (đọc content) của SKILL.md.

---

## BƯỚC 2 — Format HTML

**Rules bắt buộc:**

- ❌ KHÔNG tạo `<h1>` (title đã có trên CMS)
- ✅ Wrap toàn bộ trong `<article>`
- ✅ Giữ nguyên 100% nội dung gốc — KHÔNG thêm/bớt thông tin, KHÔNG tự suy diễn thông tin event không có trong content nguồn

**Extract các field đặc thù từ content nguồn** (không hỏi thêm tham số CLI):

| Field | Cách nhận diện trong content |
|---|---|
| Tên event | Tiêu đề chính hoặc câu mở đầu nêu tên hội thảo/workshop |
| Ngày/giờ bắt đầu (`startDate`) | Cụm ngày giờ cụ thể trong bài (ví dụ "9h ngày 20/8/2026") |
| Ngày/giờ kết thúc (`endDate`) | Nếu có nêu rõ; nếu không có → bỏ field này, KHÔNG tự đoán |
| Địa điểm | Địa chỉ cụ thể nêu trong bài; nếu không nêu rõ → dùng địa chỉ trụ sở Mắt Quốc Tế Đà Nẵng làm mặc định |
| Giá / miễn phí | Cụm từ về chi phí tham dự; nếu không nhắc đến → không sinh field `offers` |
| Link đăng ký | URL form đăng ký (Google Form, v.v.) nếu có trong content |

**Cấu trúc HTML:**

- Đoạn giới thiệu event → `<p>`
- **Info block** ngay đầu bài (sau đoạn giới thiệu, trước nội dung chi tiết), dùng `<ul>`:

```html
<ul class="event-info">
  <li><strong>Thời gian:</strong> {ngày giờ}</li>
  <li><strong>Địa điểm:</strong> {địa điểm}</li>
  <li><strong>Chi phí:</strong> {giá hoặc "Miễn phí"}</li>
</ul>
```

Chỉ đưa vào các `<li>` có dữ liệu thực tế — field nào không có trong content thì bỏ dòng đó, không để trống hoặc bịa.

- Nội dung chi tiết (nội dung chương trình, diễn giả, lý do tham gia...) → `<h2>`/`<h3>` + `<p>`/`<ul>` như bài thường
- **CTA đăng ký** — nếu có link đăng ký, chèn 1 đoạn CTA rõ ràng gần cuối bài:

```html
<p><strong>Đăng ký tham dự:</strong> <a href="{link đăng ký}" rel="nofollow" target="_blank">{anchor text tự nhiên, ví dụ "Đăng ký ngay tại đây"}</a></p>
```

---

## BƯỚC 3 — Internal Links

Chèn **1-2 internal links** liên quan (nếu event gắn với 1 dịch vụ cụ thể, ví dụ "Hội thảo Lasik" → link Femto Lasik). Dùng cùng danh sách URL hardcoded và rules format link (internal vs external) như trong `references/post.md` BƯỚC 3, mục 5-7. Không áp dụng flag `none-internal` cho event (event không có block bác sĩ tham vấn nên không cần flag này).

Không cần chèn block "bác sĩ tham vấn" (BƯỚC 3.5 của post) — event không áp dụng.

---

## BƯỚC 4 — SEO Meta Data & LSI Image Keywords

Giống post: Title (50-60 ký tự, chứa keyword/tên event), Description (150-160 ký tự, có CTA), Slug, và N LSI image keywords (mặc định 3) — modifier nên xoay quanh không khí event (hội trường, diễn giả, người tham dự, banner sự kiện) thay vì phẫu thuật/điều trị.

---

## BƯỚC 4.5 — Schema.org: Event

Luôn sinh schema `Event` cho loại bài này (không optional như FAQ/HowTo ở post):

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "{tên event}",
  "startDate": "{ISO 8601, ví dụ 2026-08-20T09:00+07:00}",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "Place",
    "name": "Bệnh viện Mắt Quốc tế DND Sài Gòn",
    "address": "{địa điểm extract được, hoặc địa chỉ trụ sở nếu content không nêu rõ}"
  },
  "image": "{để trống hoặc placeholder, điền tay sau khi có ảnh thật}",
  "description": "{description ngắn, lấy từ đoạn giới thiệu}",
  "organizer": {
    "@type": "Organization",
    "name": "Bệnh viện Mắt Quốc tế DND Sài Gòn",
    "url": "https://matquoctednd.vn/"
  }
}
```

**Field điều kiện — chỉ thêm khi content có dữ liệu, không bịa:**
- `endDate`: chỉ thêm nếu content nêu rõ giờ/ngày kết thúc
- `offers` (nested trong Event): chỉ thêm nếu có thông tin giá hoặc link đăng ký

```json
"offers": {
  "@type": "Offer",
  "price": "{số tiền, hoặc \"0\" nếu miễn phí}",
  "priceCurrency": "VND",
  "availability": "https://schema.org/InStock",
  "url": "{link đăng ký}"
}
```

Nếu event miễn phí và không có link đăng ký cụ thể → bỏ hẳn field `offers`, không sinh với giá trị giả.

**Serialize:** `json.dumps(obj, ensure_ascii=False, indent=2)`, đặt `<script type="application/ld+json">{json}</script>` ngay trước `</article>`.

---

## Output — bảng Schema.org bổ sung

| Schema | Áp dụng? | Lý do |
|---|---|---|
| Event | ✅ | Luôn sinh cho loại event |
| Event.offers | ✅/❌ | {có/không có thông tin giá hoặc đăng ký trong content} |

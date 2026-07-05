# Workflow: DOCTOR (trang thông tin bác sĩ)

Áp dụng khi type = `doctor`. Tiếp nối sau BƯỚC 1 (đọc content) của SKILL.md.

---

## BƯỚC 2 — Format HTML

**Rules bắt buộc:**

- ❌ KHÔNG tạo `<h1>` (title đã có trên CMS)
- ✅ Wrap toàn bộ trong `<article>`
- ✅ Giữ nguyên 100% nội dung gốc — KHÔNG thêm/bớt thông tin, KHÔNG tự suy diễn học vị/kinh nghiệm không có trong content nguồn

**Extract các field đặc thù từ content nguồn:**

| Field | Cách nhận diện trong content |
|---|---|
| Tên bác sĩ | Tên đầy đủ, thường ở đầu bài |
| Chức danh / học vị | "Thạc sĩ", "Bác sĩ nội trú", "Tiến sĩ", v.v. đi kèm tên |
| Chuyên khoa | Lĩnh vực chuyên môn (ví dụ "khúc xạ", "giác mạc", "phẫu thuật Lasik") |
| Nơi đào tạo | Trường/viện đào tạo nếu có nêu |
| Chức vụ hiện tại | Ví dụ "Giám đốc", "Trưởng khoa..." |
| Số năm kinh nghiệm | Nếu content nêu rõ số năm hoặc năm bắt đầu hành nghề |

Field nào content không nêu → bỏ qua, KHÔNG bịa thông tin.

**Cấu trúc HTML:**

- Đoạn giới thiệu tổng quan → `<p>`
- **Credentials block** ngay đầu bài (sau đoạn giới thiệu), dùng `<ul>`:

```html
<ul class="doctor-info">
  <li><strong>Chức danh:</strong> {chức danh/học vị}</li>
  <li><strong>Chuyên khoa:</strong> {chuyên khoa}</li>
  <li><strong>Chức vụ:</strong> {chức vụ hiện tại}</li>
  <li><strong>Kinh nghiệm:</strong> {số năm kinh nghiệm}</li>
</ul>
```

Chỉ đưa vào các `<li>` có dữ liệu thực tế trong content.

- Nội dung chi tiết (quá trình công tác, thành tích, triết lý điều trị...) → `<h2>`/`<h3>` + `<p>`/`<ul>` như bài thường
- KHÔNG cần block "bác sĩ tham vấn" (BƯỚC 3.5 của post) — trang này chính là bác sĩ, không áp dụng

---

## BƯỚC 3 — Internal Links

Chèn **1-2 internal links** đến dịch vụ mà bác sĩ này phụ trách/chuyên môn (nếu content nhắc đến, ví dụ bác sĩ chuyên Lasik → link Femto Lasik). Dùng cùng danh sách URL hardcoded và rules format link như `references/post.md` BƯỚC 3, mục 5-7. Không áp dụng flag `none-internal` cho doctor.

---

## BƯỚC 4 — SEO Meta Data & LSI Image Keywords

Title (50-60 ký tự, chứa tên bác sĩ + chuyên khoa), Description (150-160 ký tự, tóm tắt chuyên môn + CTA đặt lịch khám), Slug (từ tên bác sĩ), và N LSI image keywords (mặc định 3) — modifier nên xoay quanh: bác sĩ đang khám/tư vấn, phòng khám, khoảnh khắc với bệnh nhân, chân dung chuyên nghiệp.

---

## BƯỚC 4.5 — Schema.org: Physician

Luôn sinh schema `Physician` cho loại bài này:

```json
{
  "@context": "https://schema.org",
  "@type": "Physician",
  "name": "{tên bác sĩ, kèm chức danh nếu tự nhiên, ví dụ 'BS. Nguyễn Văn A'}",
  "medicalSpecialty": "{chuyên khoa}",
  "worksFor": {
    "@type": "Organization",
    "name": "Bệnh viện Mắt Quốc tế DND Sài Gòn",
    "url": "https://matquoctednd.vn/"
  },
  "url": "{URL trang bác sĩ trên matquoctednd.vn, nếu biết; nếu không → bỏ field này}"
}
```

**Field điều kiện — chỉ thêm khi content có dữ liệu, không bịa:**

- `alumniOf`: chỉ thêm nếu content nêu rõ nơi đào tạo

```json
"alumniOf": {
  "@type": "EducationalOrganization",
  "name": "{tên trường/viện}"
}
```

- `hasCredential`: chỉ thêm nếu content nêu rõ học vị/chứng chỉ cụ thể (ví dụ "Thạc sĩ Nhãn khoa")

```json
"hasCredential": {
  "@type": "EducationalOccupationalCredential",
  "credentialCategory": "{học vị/chứng chỉ}"
}
```

Nếu content không nêu chuyên khoa rõ ràng → vẫn có thể sinh `Physician` cơ bản (name + worksFor), bỏ field `medicalSpecialty`.

**Serialize:** `json.dumps(obj, ensure_ascii=False, indent=2)`, đặt `<script type="application/ld+json">{json}</script>` ngay trước `</article>`.

---

## Output — bảng Schema.org bổ sung

| Schema | Áp dụng? | Lý do |
|---|---|---|
| Physician | ✅ | Luôn sinh cho loại doctor |
| Physician.alumniOf | ✅/❌ | {có/không có thông tin nơi đào tạo trong content} |
| Physician.hasCredential | ✅/❌ | {có/không có thông tin học vị cụ thể trong content} |

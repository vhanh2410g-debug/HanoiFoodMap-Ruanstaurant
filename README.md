# Hanoi Food Map

## Đưa project lên GitHub

Đưa **nội dung bên trong thư mục này** vào thư mục gốc của repository `HANOI-FOOD-MAP`. Giữ nguyên cấu trúc `src/`, `data/`, `scripts/` và `.github/workflows/`.

Không cần đưa `node_modules/`, `dist/` hoặc `work/` lên GitHub. File `data/HanoiFoodPlaces.xlsx` và `src/restaurants.generated.json` cần được giữ lại để dữ liệu quán và bước đồng bộ hoạt động.

## Bật GitHub Pages

Trong repository, mở **Settings → Pages → Build and deployment** và chọn **GitHub Actions** làm nguồn deploy. Workflow trong `.github/workflows/deploy-pages.yml` sẽ build và deploy site mỗi khi có commit mới lên `main`.

Workflow đồng bộ file Excel trước khi build bằng `scripts/sync_restaurants.py`, nên cần giữ cả workbook và script trong repo.

## Chạy local

```sh
pnpm install
pnpm dev
```

Production build cho local:

```sh
pnpm build
```

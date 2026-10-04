1. Tôi dùng AWS tại region `us-east-1` (CPU node ở `us-east-1a`), instance `t3.micro`, source commit `a0de1422f9b14bda248f5ab2fa403a3202e6794f`.
2. Dataset có 284.807 dòng và 30 features; chia stratified thành 205.060 train / 22.785 validation / 56.962 test với seed 42.
3. Load dữ liệu mất 2,242 giây; training mất 3,285 giây; best iteration là 34.
4. Trên tập test: AUC 0,971671; Accuracy 0,999473; F1 0,833333; Precision 0,914634; Recall 0,765306.
5. Latency 1 dòng là 1,210 ms; throughput batch 1.000 dòng là 487.160,04 dòng/giây; đo median `predict_proba` sau warm-up qua 200 lần cho 1 dòng và 30 lần cho batch.
6. Ngay sau benchmark lúc 23:22:17 ngày 03/10/2026 (UTC+7), CPU idle 100%, RAM dùng 197,3/914 MiB, mạng `ens5` RX 279.735.019 bytes và TX 1.086.730 bytes; ảnh `screenshots/system_resources_after_benchmark.png`.
7. Ảnh Billing chụp lúc 08:49 ngày 04/10/2026 (UTC+7) hiển thị `$0.00` và 0 dịch vụ nhưng biểu đồ mới tới tháng 9, nên chi phí lab ngày 03/10 chưa cập nhật; baseline ước tính riêng là khoảng `$0.1083/giờ`; ảnh `screenshots/billing.png`.
8. Tôi đã tải kết quả trước khi dọn dẹp; `terraform destroy` hoàn tất lúc 23:45 ngày 03/10/2026 (UTC+7), xóa 27 resources và state còn 0 resources/0 outputs; bằng chứng `screenshots/terraform_destroy.png` và `cleanup_status.json`.

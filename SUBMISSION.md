# Lab 16 — AWS submission report

## Kết quả

Mô hình `LGBMClassifier` được huấn luyện và đánh giá trên bộ Credit Card Fraud Detection gồm 284,807 giao dịch. Dữ liệu được chia phân tầng thành 205,060 dòng train, 22,785 dòng validation và 56,962 dòng test. Model dừng ở iteration 34 với AUC-ROC 0.971671, Accuracy 0.999473, F1 0.833333, Precision 0.914634 và Recall 0.765306. Thời gian load dữ liệu là 2.242 giây, training là 3.285 giây trên EC2 `t3.micro`. Median latency cho một dòng là 1.210 ms; batch 1,000 dòng đạt 487,160.04 dòng/giây.

Accuracy cần được đọc cùng F1/Precision/Recall vì tỷ lệ gian lận chỉ khoảng 0.173%. Precision cao cho thấy phần lớn cảnh báo là đúng, nhưng Recall cho thấy model vẫn bỏ sót khoảng 23.47% giao dịch gian lận. Với node CPU nhỏ, tốc độ inference phù hợp cho xử lý offline hoặc micro-batch.

## Deliverables

- [x] `benchmark.py` — load/split/train/evaluate/benchmark inference.
- [x] `benchmark_result.json` — kết quả máy đọc được và thông tin môi trường.
- [x] `evidence/benchmark_terminal.txt` và `.png` — output benchmark.
- [x] `evidence/system_resources.txt` và `.png` — CPU/RAM/network/disk.
- [x] `evidence/aws_resource_inventory.json` — EC2/NAT/ALB trước cleanup.
- [x] `submission/terraform_source.zip` — Terraform source, không chứa key/state/provider cache.
- [x] Báo cáo ngắn về chất lượng và hiệu năng model.
- [x] Billing/Cost evidence — Cost Explorer được truy vấn bằng quyền read-only tạm thời nhưng trả `DataUnavailableException`; audit nằm trong `evidence/cost_explorer_status.txt` và không có số liệu giả.
- [x] `terraform destroy` — hoàn tất qua WSL: 27 resources destroyed; trạng thái được xác minh lại qua AWS API.

## Chi phí

Chi phí nền ước tính khoảng **$0.1083/giờ**, chưa gồm NAT data processing, data transfer và ALB LCU. Ước tính gồm hai `t3.micro`, một NAT Gateway, ALB base charge và bốn public IPv4. Đây là ước tính theo bảng giá AWS, không phải số Cost Explorer; không có số billing nào được tạo giả.

## Trạng thái cleanup

Terraform đã xóa thành công toàn bộ 27 resources. Do Avast Web Shield can thiệp vào mTLS loopback giữa Terraform Windows và provider, cleanup được chạy bằng cùng state trong Ubuntu WSL, không tắt antivirus. Kết quả:

- Hai EC2 instance: `terminated`.
- NAT Gateway: `deleted`.
- ALB và VPC: không còn tồn tại.
- Terraform state: 0 resources, 0 outputs.
- IAM policy Cost Explorer tạm: đã gỡ.

Log đầy đủ nằm trong `evidence/terraform_destroy.txt`; kết quả kiểm tra sau cleanup nằm trong `evidence/cleanup_status.json`.

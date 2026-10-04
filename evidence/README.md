# Evidence index

Thời điểm thu thập: 03/10/2026 (UTC+7).

| Bằng chứng | File |
|---|---|
| Output benchmark thực trên EC2 | `benchmark_terminal.txt`, `benchmark_terminal.png` |
| CPU, RAM, network, disk và EC2 metadata | `system_resources.txt`, `system_resources.png` |
| Inventory EC2/NAT/ALB trước cleanup | `aws_resource_inventory.json` |
| Trạng thái Cost Explorer và IAM policy tạm | `cost_explorer_status.txt` |
| Log Terraform cleanup hoàn chỉnh | `terraform_destroy.txt`, `terraform_destroy.png` |
| Xác minh tài nguyên sau cleanup | `cleanup_status.json` |

Các PNG là bản render nguyên văn từ output command đã thu thập, không phải ảnh dựng số liệu. Billing không có số thực tế vì Cost Explorer trả `DataUnavailableException`; trạng thái quyền tạm và việc gỡ quyền được lưu để tránh báo cáo số giả.

## Cleanup status

`terraform destroy` đã hoàn tất qua WSL: **27 resources destroyed**. Xác minh độc lập cho thấy hai EC2 đã `terminated`, NAT Gateway đã `deleted`, ALB và VPC không còn tồn tại; Terraform state còn 0 resources và 0 outputs.

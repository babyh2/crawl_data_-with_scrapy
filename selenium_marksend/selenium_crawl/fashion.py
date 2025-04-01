import json

def count_json_parts(data):
    # Kiểm tra nếu dữ liệu là danh sách (list) hoặc từ điển (dict)
    if isinstance(data, list):
        count = len(data)
        result = []
        for item in data:
            result.append(count_json_parts(item))
        return {'count': count, 'sub_parts': result}  
    elif isinstance(data, dict):
        count = len(data)
        result = {}
        for key, value in data.items():
            result[key] = count_json_parts(value) 
        return {'count': count, 'sub_parts': result} 
    
def process_json_file(input_filename, output_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)  
    result = count_json_parts(data)  
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4) 
    print(f"Kết quả đã được ghi vào {output_filename}")

process_json_file('C:\crawl_demo\selenium_marksend\product_data_02.json', 'result.json') 

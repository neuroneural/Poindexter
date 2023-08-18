source_path = '/path/to/source/nginx.conf'
destination_path = '/path/to/destination/nginx.conf'

with open(source_path, 'r') as file:
    content = file.read()
## Insert code to replace ip address with "[IP address]"
with open(destination_path, 'w') as file:
    file.write(content)

import packaging.tags
import platform
print(f"Platform: {platform.system()} {platform.release()} {platform.machine()}")
print("Supported tags:")
for tag in packaging.tags.sys_tags():
    print(tag)

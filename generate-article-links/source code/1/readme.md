检查是否有嵌套双引号的函数(功能有限，主要是正则表达式的匹配问题) => 最终还是移除了；又需要可以参考

def _check_unescaped_quotes(self, raw_content, url):
        """改进的引号检查方法，能检测嵌套引号"""
        # 改进正则表达式，更严格匹配description标签
        pattern = r'<meta\s+name=["\']description["\']\s+content=(["\'])(.*)\1' # 其中，(["\']) 捕获了开始时使用的引号类型，(.*) 则匹配引号之间的所有内容，\1 确保了结束时使用的引号与开始的类型一致。
        matches = re.finditer(pattern, raw_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            quote_type = match.group(1)
            content = match.group(2)
            
            # 检查未转义的双引号
            if quote_type == '"':
                unescaped = [m.start() for m in re.finditer(r'(?<!\\)"', content)]
                if unescaped:
                    print(f"关键警告: 文件 {url} 存在未转义双引号，位置: description, 可能是嵌套引号，请修改源文件后重新生成\n")                    # print(f"问题内容: {content}")
            
            # 检查未转义的单引号
            elif quote_type == "'":
                unescaped = [m.start() for m in re.finditer(r"(?<!\\)'", content)]
                if unescaped:
                    print(f"关键警告: 文件 {url} 存在未转义单引号，位置: description, 可能是嵌套引号，请修改源文件后重新生成\n")
                    # print(f"问题内容: {content}")
    
        # 检查整个content属性是否完整闭合
        if not matches:
            print(f"警告: 文件 {url} 的description meta标签格式异常或未闭合")

这段代码只检测内容字符串中存在的实际双引号，而不会解析 HTML 实体。对于 <meta name="description" content="hello &quot;world&quot;."> 这种情况，content 属性中的内容实际上是 hello &quot;world&quot;.，并不包含真正的双引号字符（"），而是 HTML 实体 &quot;。因此，在代码检查时，它不会检测到未转义的双引号，也就不会报出警告。
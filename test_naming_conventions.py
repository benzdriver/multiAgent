"""
测试模块命名规范
"""
import asyncio
import json
from pathlib import Path
from core.clarifier.requirement_analyzer import RequirementAnalyzer

async def test_naming_conventions():
    """测试模块命名规范是否正确应用"""
    print("开始测试模块命名规范...")
    
    analyzer = RequirementAnalyzer(output_dir="data/output/test_naming")
    
    test_input = """

系统需要一个完整的用户管理模块，包括用户注册、登录、个人资料管理等功能。

- 用户登录界面：提供用户名和密码输入
- 用户注册页面：收集用户基本信息
- 个人资料视图：展示和编辑用户信息
- 主布局：应用的主要布局结构

- 用户认证：处理用户登录和权限验证
- 用户管理：处理用户信息的增删改查
- 输入验证：验证用户输入的合法性
- 请求过滤：过滤和处理HTTP请求

- 用户数据：用户相关的数据结构
- 用户数据访问：访问用户数据的接口
- 用户数据传输：用于API的数据传输对象
- 数据访问对象：数据库访问的抽象层

- 外部API调用：与第三方服务交互
- 文件存储：处理文件上传和存储
- JWT认证：基于JWT的认证机制
- 系统日志：记录系统操作和错误
"""
    
    async def mock_llm_call(prompt, parse_response=None):
        """模拟LLM调用，返回预定义的模块列表"""
        modules = [
            {
                "module_name": "用户登录",
                "module_type": "UI组件",
                "responsibilities": ["提供用户登录界面", "验证用户输入"],
                "layer": "表现层",
                "domain": "用户管理",
                "dependencies": ["认证服务"],
                "requirements": ["用户应能够登录系统"],
                "technology_stack": ["React", "HTML", "CSS"]
            },
            {
                "module_name": "用户注册",
                "module_type": "页面",
                "responsibilities": ["收集用户注册信息", "提交注册请求"],
                "layer": "表现层",
                "domain": "用户管理",
                "dependencies": ["用户管理服务"],
                "requirements": ["用户应能够注册新账号"],
                "technology_stack": ["React", "HTML", "CSS"]
            },
            {
                "module_name": "个人资料",
                "module_type": "视图",
                "responsibilities": ["展示用户个人资料", "提供编辑功能"],
                "layer": "表现层",
                "domain": "用户管理",
                "dependencies": ["用户管理服务"],
                "requirements": ["用户应能够查看和编辑个人资料"],
                "technology_stack": ["React", "HTML", "CSS"]
            },
            {
                "module_name": "主应用",
                "module_type": "布局组件",
                "responsibilities": ["提供应用主布局", "组织页面结构"],
                "layer": "表现层",
                "domain": "全局",
                "dependencies": [],
                "requirements": ["应用应有统一的布局"],
                "technology_stack": ["React", "CSS Grid", "Flexbox"]
            },
            {
                "module_name": "认证",
                "module_type": "服务",
                "responsibilities": ["处理用户登录请求", "验证用户身份"],
                "layer": "业务层",
                "domain": "用户管理",
                "dependencies": ["用户仓储"],
                "requirements": ["系统应验证用户身份"],
                "technology_stack": ["Node.js", "Express"]
            },
            {
                "module_name": "用户管理",
                "module_type": "控制器",
                "responsibilities": ["处理用户相关请求", "调用相关服务"],
                "layer": "业务层",
                "domain": "用户管理",
                "dependencies": ["用户服务"],
                "requirements": ["系统应管理用户信息"],
                "technology_stack": ["Node.js", "Express"]
            },
            {
                "module_name": "输入",
                "module_type": "验证器",
                "responsibilities": ["验证用户输入", "防止恶意输入"],
                "layer": "业务层",
                "domain": "安全",
                "dependencies": [],
                "requirements": ["系统应验证所有用户输入"],
                "technology_stack": ["Node.js", "Joi"]
            },
            {
                "module_name": "认证",
                "module_type": "中间件",
                "responsibilities": ["拦截请求", "验证用户权限"],
                "layer": "业务层",
                "domain": "安全",
                "dependencies": ["认证服务"],
                "requirements": ["系统应保护受限资源"],
                "technology_stack": ["Node.js", "Express"]
            },
            {
                "module_name": "用户",
                "module_type": "模型",
                "responsibilities": ["定义用户数据结构", "提供数据验证"],
                "layer": "数据层",
                "domain": "用户管理",
                "dependencies": [],
                "requirements": ["系统应存储用户信息"],
                "technology_stack": ["MongoDB", "Mongoose"]
            },
            {
                "module_name": "用户",
                "module_type": "仓储",
                "responsibilities": ["提供用户数据访问", "处理数据查询"],
                "layer": "数据层",
                "domain": "用户管理",
                "dependencies": ["用户模型"],
                "requirements": ["系统应能够查询用户数据"],
                "technology_stack": ["MongoDB", "Mongoose"]
            },
            {
                "module_name": "用户",
                "module_type": "数据传输对象",
                "responsibilities": ["定义API数据结构", "处理数据转换"],
                "layer": "数据层",
                "domain": "用户管理",
                "dependencies": ["用户模型"],
                "requirements": ["系统应提供标准化的数据结构"],
                "technology_stack": ["TypeScript", "JSON"]
            },
            {
                "module_name": "用户",
                "module_type": "数据访问对象",
                "responsibilities": ["抽象数据库访问", "提供CRUD操作"],
                "layer": "数据层",
                "domain": "用户管理",
                "dependencies": ["数据库连接"],
                "requirements": ["系统应提供统一的数据访问接口"],
                "technology_stack": ["MongoDB", "Mongoose"]
            },
            {
                "module_name": "支付",
                "module_type": "API客户端",
                "responsibilities": ["与支付服务交互", "处理支付请求"],
                "layer": "基础设施层",
                "domain": "支付",
                "dependencies": [],
                "requirements": ["系统应支持在线支付"],
                "technology_stack": ["Node.js", "Axios"]
            },
            {
                "module_name": "文件",
                "module_type": "存储服务",
                "responsibilities": ["处理文件上传", "管理文件存储"],
                "layer": "基础设施层",
                "domain": "文件管理",
                "dependencies": [],
                "requirements": ["系统应支持文件上传"],
                "technology_stack": ["Node.js", "AWS S3"]
            },
            {
                "module_name": "JWT",
                "module_type": "认证服务",
                "responsibilities": ["生成JWT令牌", "验证JWT令牌"],
                "layer": "基础设施层",
                "domain": "安全",
                "dependencies": [],
                "requirements": ["系统应使用JWT进行认证"],
                "technology_stack": ["Node.js", "jsonwebtoken"]
            },
            {
                "module_name": "系统",
                "module_type": "日志服务",
                "responsibilities": ["记录系统日志", "处理错误日志"],
                "layer": "基础设施层",
                "domain": "监控",
                "dependencies": [],
                "requirements": ["系统应记录操作日志"],
                "technology_stack": ["Node.js", "Winston"]
            }
        ]
        return modules
    
    modules = await analyzer.analyze_granular_modules(test_input, mock_llm_call)
    
    naming_conventions = {
        "表现层": {
            "UI组件": "{}UI",
            "页面": "{}Page",
            "视图": "{}View",
            "布局组件": "{}Layout"
        },
        "业务层": {
            "服务": "{}Service",
            "控制器": "{}Controller",
            "验证器": "{}Validator",
            "中间件": "{}Middleware"
        },
        "数据层": {
            "模型": "{}Model",
            "仓储": "{}Repository",
            "数据传输对象": "{}DTO",
            "数据访问对象": "{}DAO"
        },
        "基础设施层": {
            "API客户端": "{}Client",
            "存储服务": "{}Storage",
            "认证服务": "{}Auth",
            "日志服务": "{}Logger"
        }
    }
    
    print("\n命名规范验证结果:")
    print("-" * 50)
    
    for module in modules:
        module_name = module.get("module_name", "")
        module_type = module.get("module_type", "")
        layer = module.get("layer", "")
        
        print(f"模块: {module_name}")
        print(f"类型: {module_type}")
        print(f"层级: {layer}")
        
        if layer in naming_conventions and module_type in naming_conventions[layer]:
            pattern = naming_conventions[layer][module_type]
            expected_suffix = pattern.format("").strip()
            
            if expected_suffix and module_name.endswith(expected_suffix):
                print(f"✓ 命名符合规范: {module_name}")
            else:
                print(f"✗ 命名不符合规范: {module_name}，应以 {expected_suffix} 结尾")
        else:
            print(f"? 未定义的层级或模块类型: {layer}/{module_type}")
        
        print("-" * 50)
    
    output_file = Path("data/output/test_naming/naming_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(modules, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到: {output_file}")
    print("测试完成!")

if __name__ == "__main__":
    asyncio.run(test_naming_conventions())

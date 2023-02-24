with open("response.html", "r+", encoding="utf8") as template_file:
    root_domain = "." + input("Enter your root domain (ex: tobycm.ga): ")
    vscode_domain = input(f"Enter your VS Code domain (default: vscode{root_domain}): ")
    if vscode_domain == "":
        vscode_domain = f"vscode{root_domain}"

    template_file.write(
        template_file.read()
        .replace("%root_domain%", root_domain)
        .replace("%vscode_domain%", vscode_domain)
    )

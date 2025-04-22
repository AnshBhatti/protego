extern "C" {
#include <breakwater/breakwater.h>
#include <breakwater/seda.h>
#include <breakwater/dagor.h>
#include <breakwater/nocontrol.h>
}

#include "breakwater/rpc++.h"
#include "cc/net.h"
#include "cc/runtime.h"

#include "cc/sync.h"

#include <memory>
#include <iostream>

netaddr server;
const struct crpc_ops *crpc_ops;
const struct srpc_ops *srpc_ops;

int StringToAddr(const char *str, uint32_t *addr) {
    uint8_t a, b, c, d;

    std::cout << "Parsing IP address: " << str << std::endl;
    if (sscanf(str, "%hhu.%hhu.%hhu.%hhu", &a, &b, &c, &d) != 4) {
        std::cerr << "Failed to parse IP address: " << str << std::endl;
        return -EINVAL;
    }

    *addr = MAKE_IP_ADDR(a, b, c, d);
    std::cout << "Parsed IP address successfully: " << str << std::endl;
    return 0;
}

void ClientHandler(void *arg) {
    std::cout << "ClientHandler started." << std::endl;

    struct rpc_session_info info = {.session_type = 0};
    std::cout << "Dialing server..." << std::endl;
    std::unique_ptr<rpc::RpcClient> conn(rpc::RpcClient::Dial(server, 1, nullptr, nullptr, &info));

    const char *message = "hello";
    std::cout << "Sending message: " << message << std::endl;
    auto ret = conn->Send(message, 5, 8423, nullptr);

    if (ret == -ENOBUFS) {
        std::cerr << "Send failed: ENOBUFS" << std::endl;
        return;
    }

    if (ret != static_cast<ssize_t>(5)) {
        std::cerr << "Send failed, ret = " << ret << std::endl;
        return;
    }

    std::cout << "Message sent successfully." << std::endl;
}

int main(int argc, char *argv[]) {
    std::cout << "Program started." << std::endl;

    rt::Mutex __dont_care;
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " client <server_ip> <# threads/conns> <config>" << std::endl;
        return -EINVAL;
    }

    std::cout << "Arguments received: " << std::endl;
    for (int i = 0; i < argc; ++i) {
        std::cout << "argv[" << i << "]: " << argv[i] << std::endl;
    }

    std::string user = argv[1];
    crpc_ops = &cbw_ops;
    srpc_ops = &sbw_ops;

    if (user.compare("client") == 0) {
        std::cout << "Running in client mode." << std::endl;

        auto ret = StringToAddr(argv[2], &server.ip);
        if (ret) {
            std::cerr << "Invalid server IP address: " << argv[2] << std::endl;
            return -EINVAL;
        }

        server.port = 8001;
        std::cout << "Server address set to: " << argv[2] << ":" << server.port << std::endl;

        std::cout << "Initializing runtime..." << std::endl;
        runtime_init(argv[4], ClientHandler, NULL);
        std::cout << "Runtime initialized." << std::endl;
    }

    std::cout << "Program finished." << std::endl;
    return 0;
}
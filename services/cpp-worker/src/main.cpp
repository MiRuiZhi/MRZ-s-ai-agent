#include <array>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <signal.h>
#include <sys/select.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

namespace fs = std::filesystem;

static std::string read_stdin() {
    std::ostringstream out;
    out << std::cin.rdbuf();
    return out.str();
}

static size_t find_json_value(const std::string& json, const std::string& key) {
    std::string quoted_key = "\"" + key + "\"";
    size_t pos = json.find(quoted_key);
    if (pos == std::string::npos) {
        return std::string::npos;
    }
    pos = json.find(':', pos + quoted_key.size());
    if (pos == std::string::npos) {
        return std::string::npos;
    }
    ++pos;
    while (pos < json.size() && std::isspace(static_cast<unsigned char>(json[pos]))) {
        ++pos;
    }
    return pos;
}

static std::string json_get_string(const std::string& json, const std::string& key, const std::string& fallback = "") {
    size_t pos = find_json_value(json, key);
    if (pos == std::string::npos || pos >= json.size() || json[pos] != '"') {
        return fallback;
    }
    ++pos;
    std::string value;
    while (pos < json.size()) {
        char c = json[pos++];
        if (c == '\\' && pos < json.size()) {
            char escaped = json[pos++];
            switch (escaped) {
                case '"': value.push_back('"'); break;
                case '\\': value.push_back('\\'); break;
                case '/': value.push_back('/'); break;
                case 'b': value.push_back('\b'); break;
                case 'f': value.push_back('\f'); break;
                case 'n': value.push_back('\n'); break;
                case 'r': value.push_back('\r'); break;
                case 't': value.push_back('\t'); break;
                default: value.push_back(escaped); break;
            }
            continue;
        }
        if (c == '"') {
            return value;
        }
        value.push_back(c);
    }
    return fallback;
}

static int json_get_int(const std::string& json, const std::string& key, int fallback) {
    size_t pos = find_json_value(json, key);
    if (pos == std::string::npos) {
        return fallback;
    }
    size_t end = pos;
    while (end < json.size() && (std::isdigit(static_cast<unsigned char>(json[end])) || json[end] == '-')) {
        ++end;
    }
    if (end == pos) {
        return fallback;
    }
    return std::stoi(json.substr(pos, end - pos));
}

static bool json_get_bool(const std::string& json, const std::string& key, bool fallback) {
    size_t pos = find_json_value(json, key);
    if (pos == std::string::npos) {
        return fallback;
    }
    if (json.compare(pos, 4, "true") == 0) {
        return true;
    }
    if (json.compare(pos, 5, "false") == 0) {
        return false;
    }
    return fallback;
}

static std::string json_escape(const std::string& value) {
    std::ostringstream out;
    for (char c : value) {
        switch (c) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(c);
                } else {
                    out << c;
                }
        }
    }
    return out.str();
}

class Sha256 {
public:
    Sha256() {
        state_ = {
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
        };
    }

    void update(const uint8_t* data, size_t len) {
        bit_len_ += static_cast<uint64_t>(len) * 8;
        for (size_t i = 0; i < len; ++i) {
            buffer_[buffer_len_++] = data[i];
            if (buffer_len_ == 64) {
                transform(buffer_.data());
                buffer_len_ = 0;
            }
        }
    }

    std::string final_hex() {
        buffer_[buffer_len_++] = 0x80;
        if (buffer_len_ > 56) {
            while (buffer_len_ < 64) buffer_[buffer_len_++] = 0;
            transform(buffer_.data());
            buffer_len_ = 0;
        }
        while (buffer_len_ < 56) buffer_[buffer_len_++] = 0;
        for (int i = 7; i >= 0; --i) {
            buffer_[buffer_len_++] = static_cast<uint8_t>((bit_len_ >> (i * 8)) & 0xff);
        }
        transform(buffer_.data());

        std::ostringstream out;
        for (uint32_t value : state_) {
            out << std::hex << std::setw(8) << std::setfill('0') << value;
        }
        return out.str();
    }

private:
    static uint32_t rotr(uint32_t value, uint32_t bits) {
        return (value >> bits) | (value << (32 - bits));
    }

    void transform(const uint8_t* chunk) {
        static const uint32_t k[64] = {
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        };
        uint32_t w[64];
        for (int i = 0; i < 16; ++i) {
            w[i] = (static_cast<uint32_t>(chunk[i * 4]) << 24)
                | (static_cast<uint32_t>(chunk[i * 4 + 1]) << 16)
                | (static_cast<uint32_t>(chunk[i * 4 + 2]) << 8)
                | static_cast<uint32_t>(chunk[i * 4 + 3]);
        }
        for (int i = 16; i < 64; ++i) {
            uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }

        uint32_t a = state_[0], b = state_[1], c = state_[2], d = state_[3];
        uint32_t e = state_[4], f = state_[5], g = state_[6], h = state_[7];
        for (int i = 0; i < 64; ++i) {
            uint32_t s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            uint32_t ch = (e & f) ^ ((~e) & g);
            uint32_t temp1 = h + s1 + ch + k[i] + w[i];
            uint32_t s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            uint32_t temp2 = s0 + maj;
            h = g; g = f; f = e; e = d + temp1;
            d = c; c = b; b = a; a = temp1 + temp2;
        }
        state_[0] += a; state_[1] += b; state_[2] += c; state_[3] += d;
        state_[4] += e; state_[5] += f; state_[6] += g; state_[7] += h;
    }

    std::array<uint32_t, 8> state_{};
    std::array<uint8_t, 64> buffer_{};
    size_t buffer_len_ = 0;
    uint64_t bit_len_ = 0;
};

static std::string sha256_file(const fs::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("cannot open file: " + path.string());
    }
    Sha256 sha;
    std::array<char, 8192> buffer{};
    while (input.good()) {
        input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
        std::streamsize count = input.gcount();
        if (count > 0) {
            sha.update(reinterpret_cast<const uint8_t*>(buffer.data()), static_cast<size_t>(count));
        }
    }
    return sha.final_hex();
}

static bool path_is_within(const fs::path& root, const fs::path& candidate) {
    auto root_it = root.begin();
    auto candidate_it = candidate.begin();
    for (; root_it != root.end(); ++root_it, ++candidate_it) {
        if (candidate_it == candidate.end() || *root_it != *candidate_it) {
            return false;
        }
    }
    return true;
}

static fs::path resolve_cwd(const std::string& cwd) {
    fs::path resolved = fs::weakly_canonical(fs::path(cwd));
    if (!fs::exists(resolved) || !fs::is_directory(resolved)) {
        throw std::runtime_error("cwd must be an existing directory: " + cwd);
    }

    const char* root_env = std::getenv("CPP_WORKER_ROOT");
    if (root_env != nullptr && std::string(root_env).size() > 0) {
        fs::path root = fs::weakly_canonical(fs::path(root_env));
        if (!fs::exists(root) || !fs::is_directory(root)) {
            throw std::runtime_error("CPP_WORKER_ROOT must be an existing directory");
        }
        if (!path_is_within(root, resolved)) {
            throw std::runtime_error("cwd is outside CPP_WORKER_ROOT: " + resolved.string());
        }
    }
    return resolved;
}

struct CommandResult {
    bool success = false;
    bool timed_out = false;
    int exit_code = -1;
    std::string output;
};

struct FileMeta {
    uintmax_t size = 0;
    fs::file_time_type modified_at{};
};

using FileSnapshot = std::map<std::string, FileMeta>;

static FileSnapshot snapshot_files(const fs::path& cwd) {
    FileSnapshot snapshot;
    if (!fs::exists(cwd)) {
        return snapshot;
    }
    for (const auto& entry : fs::recursive_directory_iterator(cwd)) {
        if (!entry.is_regular_file()) {
            continue;
        }
        fs::path rel = fs::relative(entry.path(), cwd);
        snapshot[rel.generic_string()] = FileMeta{
            entry.file_size(),
            fs::last_write_time(entry.path())
        };
    }
    return snapshot;
}

static CommandResult run_command(const std::string& command, const std::string& cwd, int timeout_seconds) {
    int pipefd[2];
    if (pipe(pipefd) != 0) {
        throw std::runtime_error("pipe failed");
    }

    pid_t pid = fork();
    if (pid < 0) {
        close(pipefd[0]);
        close(pipefd[1]);
        throw std::runtime_error("fork failed");
    }

    if (pid == 0) {
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        dup2(pipefd[1], STDERR_FILENO);
        close(pipefd[1]);
        if (!cwd.empty() && chdir(cwd.c_str()) != 0) {
            _exit(127);
        }
        execl("/bin/sh", "sh", "-c", command.c_str(), static_cast<char*>(nullptr));
        _exit(127);
    }

    close(pipefd[1]);
    CommandResult result;
    auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(timeout_seconds);
    bool child_done = false;
    int status = 0;

    while (!child_done) {
        char buffer[4096];
        fd_set read_set;
        FD_ZERO(&read_set);
        FD_SET(pipefd[0], &read_set);
        timeval tv{};
        tv.tv_sec = 0;
        tv.tv_usec = 100000;
        int ready = select(pipefd[0] + 1, &read_set, nullptr, nullptr, &tv);
        if (ready > 0 && FD_ISSET(pipefd[0], &read_set)) {
            ssize_t count = read(pipefd[0], buffer, sizeof(buffer));
            if (count > 0) {
                result.output.append(buffer, static_cast<size_t>(count));
            }
        }

        pid_t wait_result = waitpid(pid, &status, WNOHANG);
        if (wait_result == pid) {
            child_done = true;
            break;
        }
        if (std::chrono::steady_clock::now() > deadline) {
            kill(pid, SIGKILL);
            waitpid(pid, &status, 0);
            result.timed_out = true;
            child_done = true;
            break;
        }
    }

    char drain_buffer[4096];
    while (true) {
        fd_set drain_set;
        FD_ZERO(&drain_set);
        FD_SET(pipefd[0], &drain_set);
        timeval drain_tv{};
        int ready = select(pipefd[0] + 1, &drain_set, nullptr, nullptr, &drain_tv);
        if (ready <= 0 || !FD_ISSET(pipefd[0], &drain_set)) {
            break;
        }
        ssize_t count = read(pipefd[0], drain_buffer, sizeof(drain_buffer));
        if (count <= 0) {
            break;
        }
        result.output.append(drain_buffer, static_cast<size_t>(count));
    }
    close(pipefd[0]);

    if (result.timed_out) {
        result.exit_code = -1;
        result.success = false;
    } else if (WIFEXITED(status)) {
        result.exit_code = WEXITSTATUS(status);
        result.success = result.exit_code == 0;
    } else if (WIFSIGNALED(status)) {
        result.exit_code = 128 + WTERMSIG(status);
        result.success = false;
    }
    return result;
}

static std::string collect_files_json(const fs::path& cwd, const FileSnapshot& baseline) {
    std::ostringstream out;
    out << "[";
    bool first = true;
    if (fs::exists(cwd)) {
        for (const auto& entry : fs::recursive_directory_iterator(cwd)) {
            if (!entry.is_regular_file()) {
                continue;
            }
            fs::path rel = fs::relative(entry.path(), cwd);
            std::string rel_name = rel.generic_string();
            FileMeta current{
                entry.file_size(),
                fs::last_write_time(entry.path())
            };
            auto previous = baseline.find(rel_name);
            if (
                previous != baseline.end()
                && previous->second.size == current.size
                && previous->second.modified_at == current.modified_at
            ) {
                continue;
            }
            if (!first) {
                out << ",";
            }
            first = false;
            out << "{"
                << "\"name\":\"" << json_escape(rel_name) << "\","
                << "\"path\":\"" << json_escape(entry.path().string()) << "\","
                << "\"size\":" << entry.file_size() << ","
                << "\"sha256\":\"" << sha256_file(entry.path()) << "\""
                << "}";
        }
    }
    out << "]";
    return out.str();
}

int main() {
    try {
        std::string payload = read_stdin();
        std::string command = json_get_string(payload, "command");
        std::string cwd = resolve_cwd(json_get_string(payload, "cwd", ".")).string();
        int timeout_seconds = json_get_int(payload, "timeoutSeconds", 120);
        bool collect_files = json_get_bool(payload, "collectFiles", true);
        if (command.empty()) {
            throw std::runtime_error("command is required");
        }

        FileSnapshot baseline = collect_files ? snapshot_files(fs::path(cwd)) : FileSnapshot{};
        CommandResult command_result = run_command(command, cwd, timeout_seconds);
        std::cout << "{"
                  << "\"success\":" << (command_result.success ? "true" : "false") << ","
                  << "\"exitCode\":" << command_result.exit_code << ","
                  << "\"timedOut\":" << (command_result.timed_out ? "true" : "false") << ","
                  << "\"stdout\":\"" << json_escape(command_result.output) << "\","
                  << "\"stderr\":\"\","
                  << "\"files\":" << (collect_files ? collect_files_json(fs::path(cwd), baseline) : "[]")
                  << "}" << std::endl;
        return 0;
    } catch (const std::exception& exc) {
        std::cout << "{"
                  << "\"success\":false,"
                  << "\"exitCode\":-1,"
                  << "\"timedOut\":false,"
                  << "\"stdout\":\"\","
                  << "\"stderr\":\"" << json_escape(exc.what()) << "\","
                  << "\"files\":[]"
                  << "}" << std::endl;
        return 1;
    }
}

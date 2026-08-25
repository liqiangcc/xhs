#include <cassert>
#include <iostream>
#include <vector>

struct ListNode {
    int val;
    ListNode* next;
};

ListNode* middleNode(ListNode* head) {
    ListNode* slow = head;
    ListNode* fast = head;
    while (fast != nullptr && fast->next != nullptr) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}

static void checkLength(int n) {
    std::vector<ListNode> nodes;
    nodes.reserve(n);
    for (int i = 0; i < n; ++i) nodes.push_back({i, nullptr});
    for (int i = 0; i + 1 < n; ++i) nodes[i].next = &nodes[i + 1];
    std::vector<ListNode*> before;
    for (int i = 0; i < n; ++i) before.push_back(nodes[i].next);
    ListNode* head = n == 0 ? nullptr : &nodes[0];
    ListNode* got = middleNode(head);
    if (n == 0) {
        assert(got == nullptr);
    } else {
        assert(got == &nodes[n / 2]);
        assert(got->val == n / 2);
    }
    for (int i = 0; i < n; ++i) assert(nodes[i].next == before[i]);
}

int main() {
    for (int n = 0; n <= 20; ++n) checkLength(n);
    checkLength(999);
    checkLength(1000);
    checkLength(1001);
    std::cout << "PASS lengths=0..20,999,1000,1001 second-middle-even topology-unchanged" << std::endl;
}

package treebuild

import "fmt"

type Node struct { Val int; Left, Right *Node }

func BuildLevelOrder(vals []*int) (*Node,error) {
    if len(vals)==0 { return nil,nil }
    if vals[0]==nil {
        for _,v:=range vals[1:] { if v!=nil { return nil,fmt.Errorf("unreachable non-nil node after nil root") } }
        return nil,nil
    }
    root:=&Node{Val:*vals[0]}; queue:=[]*Node{root}; next:=1
    for len(queue)>0 && next<len(vals) {
        p:=queue[0]; queue=queue[1:]
        if next<len(vals) { if vals[next]!=nil { p.Left=&Node{Val:*vals[next]}; queue=append(queue,p.Left) }; next++ }
        if next<len(vals) { if vals[next]!=nil { p.Right=&Node{Val:*vals[next]}; queue=append(queue,p.Right) }; next++ }
    }
    for ;next<len(vals);next++ { if vals[next]!=nil { return nil,fmt.Errorf("unreachable non-nil node at slot %d",next) } }
    return root,nil
}

func LevelOrder(root *Node) [][]int {
    if root==nil { return [][]int{} }
    result:=make([][]int,0); queue:=[]*Node{root}
    for len(queue)>0 { width:=len(queue); level:=make([]int,0,width); for i:=0;i<width;i++ { n:=queue[0]; queue=queue[1:]; level=append(level,n.Val); if n.Left!=nil { queue=append(queue,n.Left) }; if n.Right!=nil { queue=append(queue,n.Right) } }; result=append(result,level) }
    return result
}

package treebuild

import (
    "fmt"
    "math/rand"
    "reflect"
    "testing"
)

func ip(v int)*int { x:=v; return &x }

func oracleLevels(root *Node) [][]int {
    out:=[][]int{}
    var dfs func(*Node,int)
    dfs=func(n *Node,d int){ if n==nil{return}; for len(out)<=d { out=append(out,[]int{}) }; out[d]=append(out[d],n.Val); dfs(n.Left,d+1); dfs(n.Right,d+1) }
    dfs(root,0); return out
}

func encode(root *Node) []*int {
    if root==nil { return []*int{} }
    vals:=[]*int{ip(root.Val)}; q:=[]*Node{root}
    for len(q)>0 { p:=q[0]; q=q[1:]; if p.Left!=nil { vals=append(vals,ip(p.Left.Val)); q=append(q,p.Left) } else { vals=append(vals,nil) }; if p.Right!=nil { vals=append(vals,ip(p.Right.Val)); q=append(q,p.Right) } else { vals=append(vals,nil) } }
    for len(vals)>1 && vals[len(vals)-1]==nil { vals=vals[:len(vals)-1] }
    return vals
}

func randomTree(r *rand.Rand,max int)*Node { if max<=0||r.Intn(5)==0{return nil}; root:=&Node{Val:r.Intn(21)-10}; q:=[]*Node{root}; count:=1; for len(q)>0&&count<max { p:=q[0];q=q[1:]; if count<max&&r.Intn(100)<62 { p.Left=&Node{Val:r.Intn(21)-10};q=append(q,p.Left);count++ }; if count<max&&r.Intn(100)<62 { p.Right=&Node{Val:r.Intn(21)-10};q=append(q,p.Right);count++ } }; return root }

func TestWriter(t *testing.T){
    fixed:=[]struct{vals []*int; want [][]int; invalid bool}{
        {[]*int{},[][]int{},false},
        {[]*int{nil},[][]int{},false},
        {[]*int{nil,nil,nil},[][]int{},false},
        {[]*int{nil,ip(1)},nil,true},
        {[]*int{ip(1)},[][]int{{1}},false},
        {[]*int{ip(1),ip(2),ip(3),nil,ip(4),nil,ip(5)},[][]int{{1},{2,3},{4,5}},false},
        {[]*int{ip(1),nil,nil,ip(2)},nil,true},
        {[]*int{ip(1),ip(2),nil,ip(3)},[][]int{{1},{2},{3}},false},
        {[]*int{ip(7),ip(7),ip(7)},[][]int{{7},{7,7}},false},
    }
    for i,c:=range fixed { root,err:=BuildLevelOrder(c.vals); if c.invalid { if err==nil { t.Fatalf("fixed %d expected error",i) }; continue }; if err!=nil { t.Fatalf("fixed %d err=%v",i,err) }; if got:=LevelOrder(root); !reflect.DeepEqual(got,c.want) { t.Fatalf("fixed %d got=%v want=%v",i,got,c.want) } }
    r:=rand.New(rand.NewSource(0x6200BC3E)); for i:=0;i<25000;i++ { original:=randomTree(r,1+r.Intn(80)); vals:=encode(original); rebuilt,err:=BuildLevelOrder(vals); if err!=nil { t.Fatalf("random %d err=%v",i,err) }; want:=oracleLevels(original); got:=LevelOrder(rebuilt); if !reflect.DeepEqual(got,want) { t.Fatalf("random %d got=%v want=%v vals=%v",i,got,want,vals) } }
    fmt.Println("PASS fixed=9 random_cases=25000 oracle=encode-rebuild-levels invalid_unreachable=pass nil_root=pass")
}

public final class StringAddition {
    private StringAddition() {}
    public static String add(String first,String second){
        validate(first);validate(second);int i=first.length()-1,j=second.length()-1,carry=0;StringBuilder r=new StringBuilder(Math.max(first.length(),second.length())+1);
        while(i>=0||j>=0||carry!=0){int a=i>=0?first.charAt(i--)-'0':0;int b=j>=0?second.charAt(j--)-'0':0;int sum=a+b+carry;r.append((char)('0'+sum%10));carry=sum/10;}
        if(r.length()==0)return "0";r.reverse();int p=0;while(p<r.length()-1&&r.charAt(p)=='0')p++;return r.substring(p);
    }
    private static void validate(String value){if(value==null)throw new IllegalArgumentException("non-null decimal string required");for(int i=0;i<value.length();i++){char ch=value.charAt(i);if(ch<'0'||ch>'9')throw new IllegalArgumentException("decimal digits only");}}
}

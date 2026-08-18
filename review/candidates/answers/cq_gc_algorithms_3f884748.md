<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_gc_algorithms_3f884748","version":2,"status":"draft","updated_at":"2026-08-19","answer_type":"concept","quality_tier":"candidate"} -->
# JVM 常规垃圾回收生法

## 核心结记

兆区分刚(���~랆�n{�R۞R��T��与**ب关体收囔器**。面试里常说的“标记-清代、复制老标记-�理”是在解祄“识别存活对象后，空间怎么回帶”的基憝理念；Serial、�arallel、G1、ZGC 则是 HotSpot 的具体收集器，它们会组合分代、并行、并发、搬迁-压缫等机制，不能把一个收囔器简南等同其一种基础所法。
- **标记-清代…* ：保留存活对象原位置，回收不可达对象占用的空间；优点是不用搬存活对象，代价是空间可能片。
- **yi#yb-���+:/ꊊ��&����kf9�.�k�z,hy���b�9b,9�빨!��n�e�9�%��빨!�c.�+�{�#9a�y�m9/d�i#y�*9��9�n�e�;�&���9k�y�$�o��b,:/���y�n�e�;�#9/a��$9�+9.#�g :)�y�+:/�y�9kf9�.�k�z,hza��d�9�빨!��n�e�9�"yal�� ��H
���!�c��y�m9�!��c���*��)��;�&��!�+�9d#����b�9nm�c���)�kf9�.�k�z,h{�#:#��o��/��/���y�9�n�a�9�n�e�;�&�k���*9�+:/�yd�9o%y�*9��9��9m�y/g9�h�c�裹�a����b-�� ��H
��X�nK�2����ɮK��i��z��Y��zx�(	�Y��iKnX��K��(	���Έ�i��{�N{�~z�nyZ^8$��E7�BKɮyJ�X�nK�266fV�v��~8Z���[�N��>z؞K�h����h��[z^K��KɎXX����K��Yʎi�NX��;�K�~yI�ZJ~��iKnY�NXh^Zَy�NXʾY��8 �6���]
O�
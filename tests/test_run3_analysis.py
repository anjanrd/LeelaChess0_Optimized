"""CPU-only proof/mapping safeguards for analysis, no engine execution."""
import unittest
from analysis.person_a.run3_systems import precision, sparse_tactic, metadata_nodes, selected_region, descriptives


class AnalysisProofTests(unittest.TestCase):
    def test_float_output_does_not_hide_integer_gemm_operands(self):
        layer = {'LayerType': 'gemm', 'Inputs': [{'Format/Datatype': 'Int8'}],
                 'Outputs': [{'Format/Datatype': 'Float'}], 'TacticName': 'sm80_xmma_gemm_i8f32_i8i32_f32'}
        self.assertEqual(precision(layer), 'int8')

    def test_opaque_fused_region_is_not_declared_fp16_from_its_boundary(self):
        self.assertEqual(precision({'LayerType': 'kgen', 'Inputs': [{'Format/Datatype': 'Half'}],
                                   'TacticName': '_gemm_mha_v2'}), 'opaque')

    def test_sparse_selection_requires_a_selected_tactic(self):
        self.assertFalse(sparse_tactic({'Name': 'sparse_model', 'TacticName': 'sm80_xmma_gemm_i8i8'}))
        self.assertTrue(sparse_tactic({'TacticName': 'sm80_xmma_fprop_sparse_conv_sptensor16'}))

    def test_metadata_mapping_prefers_one_gemm_and_refuses_ambiguity(self):
        layers = [{'LayerType': 'kgen'}, {'LayerType': 'gemm'}, {'LayerType': 'gemm'}]
        self.assertEqual(selected_region('x', [0, 1], layers), 1)
        self.assertIsNone(selected_region('x', [1, 2], layers))
        self.assertEqual(metadata_nodes({'Metadata': '[ONNX Layer: /a]\x1f[ONNX Layer: /b]'}), {'/a', '/b'})

    def test_repeat_spread_keeps_all_samples(self):
        d = descriptives([1, 2, 100]); self.assertEqual(d['median'], 2)
        self.assertEqual(d['min'], 1); self.assertEqual(d['max'], 100)


if __name__ == '__main__': unittest.main()

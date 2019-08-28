# Custom TFX Component

## When to create a custom component?

Our new component needs inputs which are different than any existing component,
including the standard components. Because of that we can’t simply use a custom
executor in an existing component, so we will need to create a completely new
custom component.

## How to create a custom component?

Before writing any code, we need to figure out:

*   The input and output artifacts of the new component based on where we want
    to put it in the existing TFX pipeline
*   The parameters we need to pass in to the new component for execution

Next, we will build the custom component and plug it into the existing pipeline
step by step.

### ComponentSpec

ComponentSpec is the class where we define the contract with detailed type info
of input and output artifacts to a component as well as the parameters that will
be used for the component execution. There are three parts in it:

*   *INPUTS*: specs for the input artifacts that will be passed into the
    component executor. Normally input artifacts are outputs from upstream
    components and thus share the same spec
*   *OUTPUTS*: specs for the output artifacts which the component will produce.
*   *PARAMETERS*: specs for the execution properties that will be passed into
    the component executor. These are non-artifact parameters that we want to
    define flexibly in the pipeline DSL and pass into execution

Here is an example of the ComponentSpec that we use.

```python
class SlackComponentSpec(types.ComponentSpec):
  """ComponentSpec for Custom TFX Slack Component."""

  INPUTS = {
      'model_export': ChannelParameter(type=standard_artifacts.Model),
      'model_blessing': ChannelParameter(type=standard_artifacts.ModelBlessing),
  }
  OUTPUTS = {
      'slack_blessing': ChannelParameter(type=standard_artifacts.ModelBlessing),
  }
  PARAMETERS = {
      'slack_token': ExecutionParameter(type=Text),
      'channel_id': ExecutionParameter(type=Text),
      'timeout_sec': ExecutionParameter(type=int),
  }
```

### Executor

Next, let's write the code for our executor for the new component. We will need
to create a new subclass of base_executor.BaseExecutor and override its Do
function. In the Do function, the arguments `input_dict`, `output_dict` and
`exec_properties` that are passed in map to `INPUTS`, `OUTPUTS` and `PARAMETERS`
that we defined in ComponentSpec respectively. For `exec_properties`, we can get
the value directly through dictionary lookup; for artifacts in `input_dict` and
`output_dict`, we provide convenient function to fetch the URIs of them (see
`model_export_uri` and `model_blessing_uri` in the example) or get the artifact
object (see `slack_blessing` in the example).

```python

class Executor(base_executor.BaseExecutor):
  """Executor for Slack component."""
  ...
  def Do(self, input_dict: Dict[Text, List[types.TfxArtifact]],
         output_dict: Dict[Text, List[types.TfxArtifact]],
         exec_properties: Dict[Text, Any]) -> None:
    ...
    # Fetch execution properties from exec_properties dict.
    slack_token = exec_properties['slack_token']
    channel_id = exec_properties['channel_id']
    timeout_sec = exec_properties['timeout_sec']

    # Fetch input URIs from input_dict.
    model_export_uri = types.get_single_uri(input_dict['model_export'])
    model_blessing_uri = types.get_single_uri(input_dict['model_blessing'])

    # Fetch output artifact from output_dict.
    slack_blessing =
        types.get_single_instance(output_dict['slack_blessing'])
    ...
```

The example above only shows the part of the implementation that uses the
passed-in value, but you can see the full example in our
[GitHub repo](https://github.com/tensorflow/tfx/blob/master/tfx/examples/custom_components/slack/slack_component/executor.py).

Also don’t forget to test it before moving on to the next step! We have created
a convenience
[script](https://github.com/tensorflow/tfx/blob/master/tfx/scripts/run_executor.py)
for you to try out your executor before putting it into production. You should
write similar code to exercise unit tests for your code. As with any production
software deployment, when developing for TFX you should make sure to have good
test coverage and a strong CI/CD framework.

### Component interface

Now that we have finished the most complex part, we need to assemble these
pieces into a component interface, to enable the component to be used in a
pipeline. You only need to follow several steps:

*   Make the component interface a subclass of base_component.BaseComponent
*   Assign a class variable SPEC_CLASS with the ComponentSpec class we defined
    earlier
*   Assign a class variable EXECUTOR_CLASS with the Executor class we defined
    earlier
*   Define the __init__() function by using the args to the function to
    construct an instance of the ComponentSpec class and invoke the super
    function with the value, along with an optional name

When an instance of the component is created, type checking logic in
`base_component.BaseComponent` class will be invoked to ensure the args passed
in are compatible with the type info defined in the ComponentSpec class.

```python
from slack_component import executor

class SlackComponent(base_component.BaseComponent):
  """Custom TFX Slack Component."""

  SPEC_CLASS = SlackComponentSpec
  EXECUTOR_CLASS = executor.Executor

  def __init__(self,
               model_export: channel.Channel,
               model_blessing: channel.Channel,
               slack_token: Text,
               channel_id: Text,
               timeout_sec: int,
               slack_blessing: Optional[channel.Channel] = None,
               name: Optional[Text] = None):
    slack_blessing = slack_blessing or channel.Channel(
        type_name='ModelBlessingPath',
        artifacts=[types.TfxArtifact('ModelBlessingPath')])
    spec = SlackComponentSpec(
        slack_token=slack_token,
        channel_id=channel_id,
        timeout_sec=timeout_sec,
        model_export=model_export,
        model_blessing=model_blessing,
        slack_blessing=slack_blessing)
    super(SlackComponent, self).__init__(spec=spec, name=name)
```

### Plugging into the TFX pipeline

The last step is to plug the new custom component into an existing TFX pipeline.
Beside adding an instance of the new component, we also need to:

*   Properly wire the upstream and downstream components of the new component to
    it. This is done by referencing the outputs of the upstream component in the
    new component and referencing the outputs of the new component in downstream
    components
*   Add the new component instance to the components list when constructing the
    pipeline Figure 6 highlights the aforementioned changes. Full example can be
    found in our GitHub repo.

The example below highlights the aforementioned changes. Full example can be
found in our
[GitHub repo](https://github.com/tensorflow/tfx/blob/master/tfx/examples/custom_components/slack/slack_component/executor.py).

```python
def _create_pipeline():
  ...
  model_validator = ModelValidator(
      examples=example_gen.outputs.examples, model=trainer.outputs.output)

  slack_validator = SlackComponent(
      model_export=trainer.outputs.output,
      model_blessing=model_validator.outputs.blessing,
      slack_token=_slack_token,
      channel_id=_channel_id,
      timeout_sec=3600,
  )

  pusher = Pusher(
      ...
      model_blessing=slack_validator.outputs.slack_blessing,
      ...)

  return pipeline.Pipeline(
      ...
      components=[
          ..., model_validator, slack_validator, pusher
      ],
      ...
  )
```

### For more information

To learn more about TFX check out the
[TFX website](https://www.tensorflow.org/tfx), join the
[TFX discussion group](https://groups.google.com/a/tensorflow.org/forum/#!forum/tfx),
and watch our [TFX playlist on YouTube](https://goo.gle/2xVkwt4), and
[subscribe](https://goo.gle/2WtM7Ak) to the TensorFlow channel.

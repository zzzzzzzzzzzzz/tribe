import {
  Button,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react"
import { type SubmitHandler, useForm, Controller } from "react-hook-form"
import { useMutation, useQueryClient } from "react-query"

import { type ApiError, SkillsService, type SkillCreate } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import SkillEditor, { skillPlaceholder } from "./SkillEditor"
import { RxReset } from "react-icons/rx"

interface AddSkillProps {
  isOpen: boolean
  onClose: () => void
}

const AddSkill = ({ isOpen, onClose }: AddSkillProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    control,
    setValue,
    setError,
    clearErrors,
    formState: { errors, isSubmitting, isValid },
  } = useForm<SkillCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      description: "",
      tool_definition: skillPlaceholder,
    },
  })

  const addSkill = async (data: SkillCreate) => {
    await SkillsService.createSkill({ requestBody: data })
  }

  const mutation = useMutation(addSkill, {
    onSuccess: () => {
      showToast("Успех!", "Навык успешно создан.", "success")
      reset()
      onClose()
    },
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Что-то пошло не так.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries("skills")
    },
  })

  const onSubmit: SubmitHandler<SkillCreate> = (data) => {
    mutation.mutate(data)
  }

  const resetSkillDefinitionHandler = () => {
    setValue("tool_definition", skillPlaceholder)
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md", lg: "lg" }}
        isCentered
      >
        <ModalOverlay />
        <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Добавить навык</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isRequired isInvalid={!!errors.name}>
              <FormLabel htmlFor="name">Название</FormLabel>
              <Input
                id="title"
                {...register("name", {
                  required: "Название обязательно для заполнения.",
                  pattern: {
                    value: /^[a-zA-Z0-9_-]{1,64}$/,
                    message: "Название должно соответствовать шаблону: ^[a-zA-Z0-9_-]{1,64}$",
                  },
                })}
                placeholder="Название"
                type="text"
              />
              {errors.name && (
                <FormErrorMessage>{errors.name.message}</FormErrorMessage>
              )}
            </FormControl>
            <FormControl isRequired isInvalid={!!errors.description} mt={4}>
              <FormLabel htmlFor="description">Описание</FormLabel>
              <Input
                id="description"
                {...register("description", {
                  required: "Описание обязательно для заполнения.",
                })}
                placeholder="Описание"
                type="text"
              />
            </FormControl>
            <Controller
              rules={{ required: true }}
              control={control}
              name="tool_definition"
              render={({
                field: { onChange, value },
                fieldState: { error },
              }) => (
                <FormControl
                  isRequired
                  isInvalid={!!errors.tool_definition}
                  mt={4}
                >
                  <FormLabel htmlFor="tool_definition">
                    Определение навыка
                  </FormLabel>
                  <SkillEditor
                    onChange={onChange}
                    onError={(message) =>
                      message
                        ? setError("tool_definition", { message })
                        : clearErrors("tool_definition")
                    }
                    value={value as object}
                  />
                  <FormErrorMessage>{error?.message}</FormErrorMessage>
                  <Button
                    size="sm"
                    leftIcon={<RxReset />}
                    mt={2}
                    onClick={resetSkillDefinitionHandler}
                  >
                    Сбросить определение навыка
                  </Button>
                </FormControl>
              )}
            />
          </ModalBody>

          <ModalFooter gap={3}>
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
              isDisabled={!isValid}
            >
              Сохранить
            </Button>
            <Button onClick={onClose}>Отмена</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default AddSkill
